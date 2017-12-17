import sublime
import sublime_plugin

# Inside packages, paths are always posix regardless of the platform in use.
import posixpath as path
from collections import OrderedDict, namedtuple
import os
import re

from .validictory import validate
from .validictory import SchemaError, ValidationError

from .common import log


###----------------------------------------------------------------------------


# A representation of all of the help available for a particular package.
#
# This tells us all of the information we need about the help for a package at
# load time so that we don't need to look it up later.
HelpData = namedtuple("HelpData", [
    "package", "index_file", "description", "doc_root", "help_topics",
    "help_files", "package_files", "urls", "help_toc"
])

_url_prefix_re = re.compile(r'^https?://')


###----------------------------------------------------------------------------


# The schema to validate that a help file entry in the "help_files" key of the
# help index is properly formattted.
help_file_schema = {
    "type": "object",
    "required": True,

    # Any key is allowed, but all must have values which are arrays. The first
    # item in the array must be a string and the remainder must be topic
    # dictionaries.
    "additionalProperties": {
        "type": "array",
        "items": [ { "type": "string", "required": True } ],

        "additionalItems": {
            "type": "object",
            "properties": {
                "topic":   { "type": "string", "required": True  },
                "caption": { "type": "string", "required": False }
            },
            "additionalProperties": False
        }
    }
}

# The schema to validate that the help table of contents in the "help_contents"
# key of the help index is properly formattted.
#
# NOTE: This recursively references itself in the children element. See the
# following line of code.
help_contents_schema = {
    "type": "array",
    "required": False,

    # Items must be topic dictionaries or strings. Topic dictionaries require
    # a topic key but may also contain a caption key and a children key which
    # is an array that is recursively identical to this one.
    #
    # Values that are strings are expanded to be topic dictionaries with no
    # children and an inherited caption.
    "items": {
        "type": [
            {"type": "string", "required": True },
            {
                "type": "object",
                "required": True,
                "properties": {
                    "topic":   { "type": "string", "required": True },
                    "caption": { "type": "string", "required": False },

                    # This is recursive; see below
                    "children": "help_contents_schema"
                },
                "additionalProperties": False
            }
        ]
    }
}

# The second type of item is a dictionary with a property that has the same
# format as the top level key.
help_contents_schema["items"]["type"][1]["properties"]["children"] = help_contents_schema

# The schema to validate that the list of external resources in the "externals"
# key of the help index is properly formatted.
externals_schema = {
    "type": "object",
    "required": False,

    # Any key is allowed, but all must have values which are arrays. The first
    # item in the array must be a string and the remainder must be topic
    # dictionaries.
    "additionalProperties": {
        "type": "array",
        "items": [ { "type": "string", "required": True } ],

        "additionalItems": {
            "type": "object",
            "properties": {
                "topic":   { "type": "string", "required": True  },
                "caption": { "type": "string", "required": False }
            },
            "additionalProperties": False
        }
    }
}

# The overall schema used to validate a hyperhelp index file.
index_schema = {
    "type": "object",
    "properties": {
        "description": { "type": "string", "required": False },
        "doc_root":    { "type": "string", "required": False },

        "help_files":    help_file_schema,
        "help_contents": help_contents_schema,
        "externals":     externals_schema
    },
    "additionalProperties": False
}


###----------------------------------------------------------------------------


def _import_topics(package, topics, help_topic_dict, external=False):
    """
    Parse out a dictionary of help topics from the help index and store all
    topics into the topic dictionary passed in. During the parsing, the
    contents are validated.

    When def_captions is True, topics that don't have a caption use the document
    title as the caption by default.
    """
    for help_source in help_topic_dict:
        topic_list = help_topic_dict[help_source]

        # Don't include topics from invalid externals.
        if (external
            and not _url_prefix_re.match(help_source)
            and not help_source.startswith("Packages/")):
                log("Discarding invalid external '%s' in %s",
                    help_source, package)
                continue

        default_caption = topic_list[0] if external else None

        # Skip the first entry since it's the title of the help source
        for topic_entry in topic_list[1:]:
            name = topic_entry.get("topic")
            caption = topic_entry.get("caption", None)
            if caption is None:
                caption = default_caption or "Topic %s in help source %s" % (name, help_source)

            # Turn spaces in the topic name into tabs so they match what's in
            # the buffer at run time. Saves forcing tabs in the index file.
            name = name.replace(" ", "\t").casefold()
            if name in topics:
                log("Skipping duplicate topic %s in %s:%s",
                    name, package, help_source)
            else:
                topics[name] = {
                    "topic": name,
                    "caption": caption,
                    "file": help_source
                }

        # All help sources should be in the topic list so you can jump to a
        # file by name. The help file name is the default.
        name = help_source.casefold()
        if name not in topics:
            topics[name] = {
                "topic": name,
                "caption": topic_list[0],
                "file": help_source
            }

    return topics


def _merge_externals(package, externals, topics, package_files, urls):
    """
    Merge the externals into the topic list provided. This ensures that there
    are no duplicate topics during the merge (discarding the external) while
    also splitting the externals into package file specifications and urls.
    """
    for topic, entry in externals.items():
        if topic in topics:
            log("Discarding duplicate external topic '%s' in %s:%s",
                topic, package, entry["file"])
            continue

        file = entry["file"]
        file_list = urls if _url_prefix_re.match(file) else package_files
        if file not in file_list:
            file_list.append(file)

        topics[topic] = entry


def _get_file_metadata(help_topic_dict):
    """
    Parse a dictionary of help topics from the help index and return back an
    ordered dictionary associating help file names with their titles.

    Assumes the help dictionary has already been validated.
    """
    retVal = OrderedDict()
    for file in sorted(help_topic_dict.keys()):
        retVal[file] = help_topic_dict[file][0]

    return retVal


def _get_toc_metadata(help_toc_list, topics, package):
    """
    Given the table of contents key from the help index and the complete list of
    known topics, return back a table of contents. This will extrapolate a list
    even if the incoming list is empty or non-existant.
    """
    if not help_toc_list:
        return [topics.get(topic) for topic in sorted(topics.keys())]

    def lookup_topic_entry(entry):
        """
        Expand a toc entry from the index into a full topic object.
        """
        if isinstance(entry, str):
            return entry, topics.get(entry.replace(" ", "\t"), None)

        topic = entry["topic"]
        base_obj = topics.get(topic.replace(" ", "\t").casefold(), None)
        if base_obj is None:
            return topic, None

        entry["file"] = base_obj["file"]
        entry["caption"] = entry.get("caption", base_obj["caption"])

        return topic, entry

    def expand_topic_list(item_list):
        """
        Expand an array of help topics that make up part of a table of contents
        into an array of full topic objects recursively.
        """
        retVal = list()

        for item in item_list:
            topic, info = lookup_topic_entry(item)
            if info is None:
                log("TOC for '%s' is missing topic '%s'; skipping", package, topic)
                continue

            child_topics = info.get("children", None)
            if child_topics:
                info["children"] = expand_topic_list(child_topics)

            retVal.append(info)

        return retVal

    return expand_topic_list(help_toc_list)


def _get_index_content(file_spec):
    """
    Load the index file content from the given file specification, if possible.
    The file spec can be an absolute path to a package file or a package
    resource specification pointing to one.

    Return is a tuple with the associated resource name and the content that
    was loaded, if any.
    """
    content = None
    if file_spec.startswith(sublime.packages_path()):
        index_res = os.path.relpath(file_spec, sublime.packages_path())
        index_res = os.path.join("Packages", index_res)

        try:
            with open(file_spec, 'r') as file:
                content = file.read()
        except:
            pass
    else:
        index_res = file_spec
        try:
            content = sublime.load_resource(index_res)
        except:
            pass

    return (index_res, content)


def _load_help_index(file_spec):
    """
    Given a package name and the resource filename of the hyperhelp json file,
    load the help index and return it. The return value is None on failure or
    HelpData on success.
    """
    index_res, content = _get_index_content(file_spec)
    if not index_res.casefold().startswith("packages/"):
        return log("Index source is not in a package: %s", index_res)

    package = path.split(index_res)[0].split("/")[1]

    if content is None:
        return log("Unable to load index information for '%s'", package)

    try:
        log("Loading help index for package '%s'", package)
        raw_dict = sublime.decode_value(content)
    except:
        return log("Unable to parse index information for '%s'", package)

    try:
        validate(raw_dict, index_schema)

    # The schema provided is itself broken.
    except SchemaError as error:
        return log("Error validating '%s': Invalid schema: %s", package, error)

    # One of the fields failed to validate. This generates extremely messy
    # output, but this can be fixed later.
    except ValidationError as error:
        return log("Error validating help index for '%s' in %s: %s",
                   package, error.fieldname, error)

    # Seems like validictory has a bug in which if you tell it to verify an
    # array has contents but the array is empty, it blows up. This can happen
    # if the array that provides the contents of a help file is empty, for
    # example.
    except Exception as error:
        return log("Error validating help index for '%s': %s",
                   package, error)

    # Top level index keys
    description = raw_dict.pop("description", "Help for %s" % package)
    doc_root = raw_dict.pop("doc_root", None)
    help_files = raw_dict.pop("help_files", dict())
    help_toc = raw_dict.pop("help_contents", None)
    externals = raw_dict.pop("externals", None)

    # Warn if the dictionary has too many keys
    for key in raw_dict.keys():
        log("Ignoring unknown key '%s' in index file %s", key, package)

    # If there is no document root, set it from the index resource; otherwise
    # ensure that it's normalized to appear in the appropriate package.
    if not doc_root:
        doc_root = path.split(index_res[len("Packages/"):])[0]
    else:
        doc_root = path.normpath("%s/%s" % (package, doc_root))

    # Gather the unique list of topics.
    topic_list = dict()
    _import_topics(package, topic_list, help_files)

    externals_list = dict()
    package_files = list()
    urls = list()
    if externals is not None:
        _import_topics(package, externals_list, externals, external=True)
        _merge_externals(package, externals_list, topic_list, package_files, urls)

    # Everything has succeeded.
    return HelpData(package, index_res, description, doc_root, topic_list,
        _get_file_metadata(help_files), package_files, urls,
        _get_toc_metadata(help_toc, topic_list, package))


def _scan_help_packages(help_list=None):
    """
    Scan for packages with a help index and load them. If a help list is
    provided, only the help for packages not already in the list will be
    loaded.
    """
    help_list = dict() if help_list is None else help_list
    for index_file in sublime.find_resources("hyperhelp.json"):
        pkg_name = path.split(index_file)[0].split("/")[1]
        if pkg_name not in help_list:
            result = _load_help_index(index_file)
            if result is not None:
                help_list[result.package] = result

    return help_list


###----------------------------------------------------------------------------
