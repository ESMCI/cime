import os
import sys
from datetime import date

import xmlschema

def generate_xml_from_schema(root, depth=1):
    lines = []
    prefix = ' ' * 4 * depth

    attrs = [f" {x}=\"\"" for x in root.attributes]
    attrs_comment = [f"'{x}' is {y.use}" for x, y in root.attributes.items()]

    if len(attrs_comment) > 0:
        lines.append(f"{prefix}<!-- Attributes {','.join(attrs_comment)}-->")

    min_occur, max_occur = root.occurs
    max_occur = "Unlimited" if max_occur is None else max_occur
    lines.append(f"{prefix}<!-- Occurrences min: {min_occur} max: {max_occur}-->")

    if root.type is None:
        return lines

    if root.type.has_simple_content():
        lines.append(f"{prefix}<{root.local_name}{''.join(attrs)}></{root.local_name}>")
    else:
        lines.append(f"{prefix}<{root.local_name}{''.join(attrs)}>")
        for x in root.iterchildren():
            lines.extend(generate_xml_from_schema(x, depth+1))
        lines.append(f"{prefix}</{root.local_name}>")
    
    return lines

def generate_code_block(text):
    prov = f"    <!-- Generated with {' '.join(sys.argv)} on {date.today()} -->"

    text = [".. code-block:: xml", "", prov, ""] + text

    return "\n".join(text)

if len(sys.argv) == 0:
    print(f"{0} xml-path <root element>")
    sys.exit()

schema = xmlschema.XMLSchema(sys.argv[1])

item_map = {x: y for x, y in schema.elements.items()}
item_map.update({x: y for x, y in schema.attributes.items()})

if len(sys.argv) < 3:
    print("\n".join(sorted(item_map)))
else:
    root = schema.find(sys.argv[2])
    schema_text = generate_xml_from_schema(root)

    text = generate_code_block(schema_text)

    print(text)