import sublime
import sublime_plugin

# Inside packages, paths are always posix regardless of the platform in use.
import posixpath as path
from collections import OrderedDict, namedtuple

from .core import log


###----------------------------------------------------------------------------


# A representation of all of the help available for a particular package.
#
# This tells us all of the information we need about the help for a package at
# load time so that we don't need to look it up later.
HelpData = namedtuple("HelpData", [
    "package", "index_file", "description", "doc_root",
    "help_files", "help_topics", "help_toc"
])


###----------------------------------------------------------------------------


def _import_topics(package, topics, help_topic_dict):
    """
    Parse out a dictionary of help topics from the help index and store all
    topics into the topic dictionary passed in. During the parsing, the
    contents are validated.
    """
    for help_source in help_topic_dict:
        topic_list = help_topic_dict[help_source]

        # Help file entry must be a list.
        if not isinstance(topic_list, list):
            return log("Help index information not a list in %s:%s",
                       package, help_source)

        # First item must be a string that is the help file title
        if not isinstance(topic_list[0], str):
            return log("First entry not a help file title string in %s:%s",
                       package, help_source)

        # Skip the first entry since it's the name of the help file
        for topic_entry in topic_list[1:]:
            if not isinstance(topic_entry, dict):
                return log("Help entry not a dictionary in %s:%s",
                           package, help_source)

            name = topic_entry.get("topic", None)
            caption = topic_entry.get("caption", None)

            if name is None:
                return log("Help topic missing topic text in %s:%s",
                            package, help_source)

            if caption is None:
                caption = "Topic %s in help file %s" % (name, help_source)

            # Turn spaces in the topic name into tabs so they match what's in
            # the buffer at run time. Saves forcing tabs in the index.
            name = name.replace(" ", "\t")
            if name in topics:
                log("Skipping duplicate topic %s in %s:%s",
                    name, package, help_source)
            else:
                topics[name] = {
                    "topic": name,
                    "caption": caption,
                    "file": help_source
                }

    return topics


def _get_file_metadata(help_topic_dict):
    """
    Parse a dictionary of help topics from the help index and return back an
    ordered dictionary associating help file names with their titles.

    Assumes the help dictionary has already been validated.
    """
    retVal = OrderedDict()
    for file in help_topic_dict:
        retVal[file] = help_topic_dict[file][0]

    return retVal


def _load_help_index(package, index_res):
    """
    Given a package name and the resource filename of the hyperhelp json file,
    load the help index and return it. The return value is None on failure or
    HelpData on success
    """
    try:
        log("Loading help index for package %s", package)
        json = sublime.load_resource(index_res)
        raw_dict = sublime.decode_value(json)
    except:
        return log("Unable to load help index information from %s", package)

    # Top level index keys
    description = raw_dict.pop("description", "No description provided")
    doc_root = raw_dict.pop("doc_root", None)
    help_files = raw_dict.pop("help_files", dict())
    help_toc = raw_dict.pop("help_contents", None)

    # Warn if the dictionary has too many  keys
    for key in raw_dict.keys():
        log("Ignoring unknown key '%s' in index file %s", key, package)

    # If there is no document root, set it from the index resource; otherwise
    # ensure that it's normalized to appear in the appropriate package.
    if doc_root is None:
        doc_root = path.split(index_res)[0]
    else:
        doc_root = path.normpath("Packages/%s/%s" % (package, doc_root))

    # Gather the unique list of topics. If any fail, no help is allowed.
    topic_list = dict()
    if _import_topics(package, topic_list, help_files):
        return HelpData(package, index_res, description, doc_root,
            _get_file_metadata(help_files), topic_list, help_toc)


###----------------------------------------------------------------------------
