from enum import Enum
from dataclasses import dataclass
from typing import Generator, Optional, TypeAlias, Union


# Split with terminator semantics
def split_with_ts(s):
    len_s = len(s)
    pos = 0
    while pos < len_s:
        new_pos = s.find("\n", pos)
        if new_pos == -1:
            # newline character not found anymore
            new_pos = len_s - 1
        yield s[pos:new_pos + 1]
        pos = new_pos + 1


def split_with_ts_bytes(s: bytes) -> Generator[bytes, None, None]:
    len_s = len(s)
    pos = 0
    while pos < len_s:
        new_pos = s.find(b"\n", pos)
        if new_pos == -1:
            # newline character not found anymore
            new_pos = len_s - 1
        yield s[pos:new_pos + 1]
        pos = new_pos + 1


class LineType(Enum):
    EMPTY = 1
    COMMENT = 2
    HEADER = 3  # TODO rename to SECTION_HEADER
    # "man git-config" uses the nomenclature inconsistently. It uses 'name' and
    # 'key' for the same thing.  We stick to "key" here. It's "key (name)".
    KEY_VALUE = 4


@dataclass(frozen=True)
class LineDataKeyValue:
    key: bytes
    value: bytes


@dataclass(frozen=True)
class LineDataHeader:
    section_name: bytes
    subsection_name: Optional[bytes]


@dataclass(frozen=True)
class LineDataEmpty:
    pass


@dataclass(frozen=True)
class ConfigLine:
    line_orig: bytes
    # NOTE: Here I would really like to have rust enums. Actually the tagged
    # union approach is just a work around.
    # TODO hmm, maybe I should use "instanceof" instead?
    line_type: LineType
    line_data: Union[LineDataKeyValue, LineDataHeader, LineDataEmpty]


GeneratorConfigLine: TypeAlias = Generator[ConfigLine, None, None]


# config format of git is descriped here
#   https://git-scm.com/docs/git-config#_configuration_file
#
# Parse git-style config file.
# See https://git-scm.com/docs/git-config
# The syntax is described here:
#    https://git-scm.com/docs/git-config/2.12.5#_syntax
# Goal: The parsed result can be converted back to the lines object with a 1to1 mapping
# NOTES:
# - not supporting "[section.subsection]" syntax
# - not supporting continouation lines yet
# - not supporting comments at end of line yet.
# - every line in lines, ends with a "\n" character
#   Only the last line may not have a trailing "\n" character.
# TODO add errors on invalid syntax
def config_parse2(lines: Generator[bytes, None, None]) -> GeneratorConfigLine:
    def get_first(b: bytes) -> Optional[int]:
        if len(b) == 0:
            return None
        return b[0]

    for line in lines:
        first_char = get_first(line.lstrip())
        if first_char is None:
            # It's an empty line
            yield ConfigLine(line, LineType.EMPTY, LineDataEmpty())
        else:
            if first_char in (ord(b'#'), ord(b';')):
                yield ConfigLine(line, LineType.COMMENT, LineDataEmpty())
            elif first_char == ord(b'['):
                # section start, like: "[section]\n"
                # Parse section name
                # TODO Check for valid section characters
                inner_part = line.split(b'[', 1)[1].split(b']')[0]
                if ord(b'"') in inner_part:
                    # There is a subsection:
                    #     [section  "subsection"]
                    section_name = inner_part.split(b'"')[0].strip()
                    subsection_name = inner_part.split(b'"', 2)[1]
                else:
                    section_name = inner_part
                    subsection_name = None

                yield ConfigLine(line, LineType.HEADER, LineDataHeader(section_name, subsection_name))
            else:
                # This is mostly a variable line
                #     key = value
                parts = line.split(b"=", 1)
                key = parts[0].strip()
                value = parts[1].strip()
                yield ConfigLine(line, LineType.KEY_VALUE, LineDataKeyValue(key, value))


# Small hepler to get type rights for pyright
def empty_config_lines() -> GeneratorConfigLine:
    if False:
        yield None


def config_unparse2(config_lines: GeneratorConfigLine) -> bytes:
    s = b""
    for config_line in config_lines:
        # TODO: This is really strange here. The data structure ConfigLine contains
        # redundant information
        s += config_line.line_orig
    return s


# TODO add support for subsection
# Requirement: section already exists
# Optional arguments
#  - "append": Whether to replace a existing key with the value or
def config_set_key_value2(config_lines: GeneratorConfigLine, section_name: bytes, key: bytes, value: bytes, append: bool = False) -> GeneratorConfigLine:
    # TODO sanitize 'key' and 'value'
    # HACK: Use list to have a mutable value
    was_emit = [False]

    def emit():
        if was_emit[0]:
            return
        # TODO adding \t is wired here. Maybe the config files does not use the
        # indentation as convention.
        yield ConfigLine(b"\t%s = %s\n" % (key, value), LineType.KEY_VALUE, LineDataKeyValue(key, value))
        was_emit[0] = True

    config_in_section = False
    for config_line in config_lines:
        if not config_in_section:
            if config_line.line_type == LineType.HEADER:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataHeader)
                # TODO support subsection!
                if line_data.section_name == section_name and line_data.subsection_name is None:
                    config_in_section = True
            yield config_line
        else:
            if config_line.line_type == LineType.HEADER:
                # New section starts
                yield from emit()
                # TODO check if the section has the same name!
                config_in_section = False
                yield config_line
            elif config_line.line_type == LineType.KEY_VALUE:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataKeyValue)
                if line_data.key == key:
                    if append:
                        # We have to append the value
                        if line_data.value > value:
                            yield from emit()
                            yield config_line
                        else:
                            yield config_line
                            yield from emit()
                    else:
                        # We have to replace the value
                        yield from emit()
                elif line_data.key > key:
                    # The current key is bigger. Emit the key-value before it
                    yield from emit()
                    yield config_line
                else:
                    yield config_line
            else:
                yield config_line

    if config_in_section:
        yield from emit()
    else:
        if not was_emit[0]:
            raise Exception("Error: No section with name '%s' found!" % (section_name.decode("utf8"),))


def config_drop_key2(config_lines: GeneratorConfigLine, section_name: bytes, key: bytes) -> GeneratorConfigLine:
    config_in_section = False
    for config_line in config_lines:
        if not config_in_section:
            if config_line.line_type == LineType.HEADER:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataHeader)
                # TODO support subsection!
                if line_data.section_name == section_name and line_data.subsection_name is None:
                    config_in_section = True
            yield config_line
        else:
            if config_line.line_type == LineType.HEADER:
                # New section starts
                config_in_section = False
                yield config_line
            elif config_line.line_type == LineType.KEY_VALUE:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataKeyValue)
                if line_data.key == key:
                    # Key found. Do drop by not yielding it
                    pass
                else:
                    yield config_line
            else:
                yield config_line


def config_drop_section_if_empty(config_lines: GeneratorConfigLine, section_name: bytes) -> GeneratorConfigLine:
    config_in_section = False
    config_line_saved = None
    for config_line in config_lines:
        if not config_in_section:
            if config_line.line_type == LineType.HEADER:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataHeader)
                # TODO support subsection!
                if line_data.section_name == section_name and line_data.subsection_name is None:
                    # We have found the section!
                    # So we don't yield it here, we have to wait for the first key in this section
                    # Otherwise we can drop it
                    config_in_section = True
                    config_line_saved = config_line
                else:
                    yield config_line
            else:
                yield config_line
        else:
            if config_line.line_type == LineType.HEADER:
                # New section starts
                config_in_section = False
                yield config_line
            elif config_line.line_type == LineType.KEY_VALUE:
                line_data = config_line.line_data
                assert isinstance(line_data, LineDataKeyValue)
                # Ok. We are in the section and we have found a key. So the section is not empty.
                # So also yield the header line of this section, if not already done
                if config_line_saved is not None:
                    yield config_line_saved
                    config_line_saved = None
                yield config_line
            else:
                yield config_line


def config_add_section2(config_lines: GeneratorConfigLine, section_name: bytes) -> GeneratorConfigLine:
    # TODO find better name for 'was_emit'
    was_emit = [False]

    def emit():
        if was_emit[0]:
            return
        yield ConfigLine(b"[%s]\n" % (section_name,), LineType.HEADER, LineDataHeader(section_name, None))
        was_emit[0] = True

    for config_line in config_lines:
        if config_line.line_type == LineType.HEADER:
            line_data = config_line.line_data
            assert isinstance(line_data, LineDataHeader)
            if line_data.section_name > section_name and line_data.subsection_name is None:
                # The next section name is bigger. Emit here!
                yield from emit()
                yield config_line
            elif line_data.section_name == section_name and line_data.subsection_name is None:
                # This section matches exactly. The section already exists. So do nothing!
                was_emit[0] = True
                yield config_line
            else:
                yield config_line
        else:
            yield config_line

    yield from emit()
