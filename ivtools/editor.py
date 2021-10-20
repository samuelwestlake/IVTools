from ivtools.namespace import Namespace


class IVEditor(object):

    def __init__(self):
        self.data = None
        self.new_nodes = None
        self.template_nodes = None

    def read(self, file_path):
        self.data = Namespace(
            {
                "HEADER": self.__read_header(file_path),
                "DATA": self.__read_data(file_path)
            }
        )

    def write(self, file_path):
        self.__write_header(file_path)
        self.__write_data(file_path)

    def load_template_file(self, file_path):
        self.template_nodes = Namespace(file_path)

    def write_nodes_file(self, file_path):
        nodes = self.data.DATA.get_nodes()
        written = []
        with open(file_path, "w") as file:
            for node in nodes:
                if node not in written:
                    written.append(node)
                    file.write("%s:\n" % node)
                    for key, fields in self.template_nodes.get().items():
                        file.write("%s%s:\n" % (" " * 2, key))
                        for field, value in fields.get().items():
                            file.write("%s%s: %s\n" % (" " * 4, field, "" if value is None else value))

    def load_nodes_file(self, file_path):
        self.new_nodes = Namespace(file_path)
        print(self.new_nodes)

    def apply_nodes(self):
        self.data.DATA.apply_nodes(self.new_nodes)

    def convert(self, ext):
        new_data = Namespace(
            {
                "HEADER": self.__convert_header(ext),
                "DATA": self.__convert_data(ext)
            }
        )
        self.data = new_data

    def delete(self, node_name):
        self.data.DATA.delete(node_name, recursive=True)

    def __write_header(self, file_path):
        with open(file_path, "w") as file:
            file.writelines("%s\n\n" % self.data.HEADER)

    def __write_data(self, file_path):
        self.data.DATA.write(file_path)

    def __read_data(self, file_path):
        text = ""
        sub_space = []
        data = Namespace()
        field_open = False
        with open(file_path, "r", encoding="utf8", errors='ignore') as file:
            for line in file.readlines():
                if line.strip():
                    if sub_space and not field_open and not self.__bracket(line):
                        # One-line field
                        data.add(
                            {
                                line.strip().split()[0]: " ".join(line.strip().split()[1:])
                            },
                            sub_space=sub_space
                        )
                    else:
                        for char in line.split("#")[0] + "\n" if "#" in line else line:
                            if char == "{":
                                data, sub_space = self.__add_node(data, text, line, sub_space)
                                text = ""
                            elif char == "}":
                                sub_space = sub_space[:-2]
                                text = ""
                            elif char == "[":
                                text += char
                                field_open = True
                            elif char == "]":
                                field_open = False
                                self.__add_field(data, text, sub_space)
                                text = ""
                            else:
                                text += char
        return data

    @staticmethod
    def __add_node(data, text, line, sub_space):
        name = " ".join(text.strip().split("\n")[-1].strip().split())
        comment = " ".join(line.split("#")[1:]).strip() if line.split("#")[1:] else None
        node = "NODE_%i" % len(data.get(sub_space))
        data.add(
            {
                node: {
                    "NAME": name,
                    "COMMENT": comment,
                    "CHILDREN": {}
                }
            }, sub_space=sub_space
        )
        return data, sub_space + [node, "CHILDREN"]

    @staticmethod
    def __add_field(data, text, sub_space):
        name, value = text.split("[")
        name = name.split("{")[-1].strip()
        value = [" ".join(row.strip().split()) for row in value.split("\n") if row.strip()]
        data.add(
            {
                name: value
            },
            sub_space=sub_space
        )
        return data

    def __convert_data(self, ext):
        if ext == "iv":
            new_data = Namespace()
            for name, node in self.data.DATA.get().items():
                new_node = self.__convert_to_iv(node)
                if new_node is not None:
                    new_data.add(
                        {name: new_node}
                    )
            return new_data
        else:
            raise NotImplementedError("Sorry, only conversion to iv is supported in this version")

    def __convert_to_iv(self, node):
        # Remove some nodes
        if node.NAME.startswith("Background") or node.NAME.startswith("texCoord") or node.NAME.startswith("normal"):
            return None

        # Restructure appearance node
        if node.NAME.startswith("appearance"):
            for name, child in node.CHILDREN.__dict__.items():
                if name.startswith("NODE") and child.NAME.startswith("material"):
                    child.CHILDREN.remove("ambientIntensity")
                    node.CHILDREN.add(child.CHILDREN.__dict__)
                    node.CHILDREN.remove(name)
                    break
            node.NAME = "Material"

        # Move Coordinate3 up a level from IndexedFaceSet
        exit_flag = False
        for name, child in node.CHILDREN.__dict__.items():
            if isinstance(child, Namespace) and "NAME" in child.__dict__ and child.NAME.startswith("geometry"):
                for sub_name, sub_child in child.CHILDREN.__dict__.items():
                    if isinstance(sub_child, Namespace) and "NAME" in sub_child.__dict__ and sub_child.NAME.startswith("coord"):
                        node.CHILDREN.add(
                            {"NODE_%i" % len(child.CHILDREN): sub_child}
                        )
                        child.CHILDREN.remove(sub_name)
                        exit_flag = True
                        break
            if exit_flag is True:
                break

        # Convert this node
        new_node = Namespace(
            {
                "NAME": self.__convert_name(node.NAME, node.COMMENT, "iv"),
                "COMMENT": node.COMMENT,
                "CHILDREN": {}
            }
        )
        # Convert the child nodes
        for name, child in node.CHILDREN.__dict__.items():
            if name.startswith("NODE"):
                new_child = self.__convert_to_iv(child)
            # Filter some fields
            elif node.NAME.startswith("geometry") and name in ["ccw", "convex", "solid"]:
                new_child = None
            else:
                new_child = child
            if new_child is not None:
                new_node.CHILDREN.add({name: new_child})

        # Swap the child node orders
        material = None
        coord3 = None
        # get the manes of coordinate3 and material
        for name, child in new_node.CHILDREN.__dict__.items():
            if name.startswith("NODE") and child.NAME.startswith("Coordinate3"):
                coord3 = name
            elif name.startswith("NODE") and child.NAME.startswith("Material"):
                material = name
        # make a new children namespace
        new_child = Namespace()
        # Add the material
        if material is not None:
            new_child.add({material: new_node.CHILDREN.get(material)})
        # Add the material
        if coord3 is not None:
            new_child.add({coord3: new_node.CHILDREN.get(coord3)})
        # Add the rest
        for name, child in new_node.CHILDREN.__dict__.items():
            if name != material and name != coord3:
                new_child.add({name: child})
        new_node.CHILDREN = new_child
        return new_node

    @staticmethod
    def __convert_name(name, comment, ext):
        if ext == "iv":
            if name.startswith("Shape"):
                return "DEF %s Separator" % comment
            if name.startswith("coord"):
                return "Coordinate3"
            if name.startswith("geometry IndexedFaceSet"):
                return "IndexedFaceSet"
        #elif name.startswith("material"):
        #    return "Material"
        #elif name.startswith("coord"):
        #    return "Coordinate3"
        #else:
        #    return name
        return name

    @staticmethod
    def __convert_fields(fields, node):
        if node == "Material" or node.startswith("material"):
            return [field for field in fields if not field.startswith("ambientIntensity")]
        else:
            return fields

    @staticmethod
    def __convert_header(ext):
        if ext == "iv":
            return "#Inventor V2.1 ascii"
        elif ext == "wrl":
            return "#VRML V2.0 utf8"

    @staticmethod
    def __bracket(x):
        if any([item in x for item in ["{", "[", "(", "}", "]", ")"]]):
            return True
        else:
            return False

    @staticmethod
    def __get_name(line):
        if "#" in line:
            return line.replace("{", "").strip()
        else:
            return line.split("{")[0].strip()

    @staticmethod
    def __read_header(file_path):
        header = ""
        with open(file_path, "r", encoding="utf8", errors='ignore') as file:
            for line in file.readlines():
                line = line.strip()
                if "{" in line:
                    break
                elif line and line.startswith("#"):
                    header += line
        return header


if __name__ == "__main__":

    editor = IVEditor()
    while True:
        try:
            cmd = input("> ")
            if cmd in ["q", "quit", "exit"]:
                break
            cmd = cmd.split(" ")
            if cmd[0] == "read":
                editor.read(" ".join(cmd[1:]))
                print("Done")
            elif cmd[0] == "write":
                editor.write(" ".join(cmd[1:]))
                print("Done")
            elif cmd[0] == "write_nodes_file":
                editor.write_nodes_file(" ".join(cmd[1:]))
                editor.load_nodes_file(" ".join(cmd[1:]))
                editor.new_nodes.summary()
                print("Done")
            elif cmd[0] == "set_nodes":
                editor.load_template_file(" ".join(cmd[1:]))
                editor.template_nodes.summary()
                print("Done")
            elif cmd[0] == "load_nodes_file":
                editor.load_nodes_file(" ".join(cmd[1:]))
                editor.new_nodes.summary()
                print("Done")
            elif cmd[0] == "apply_nodes":
                editor.apply_nodes()
                print("Done")
            elif cmd[0] == "convert":
                editor.convert(cmd[1])
                print("Done")
            elif cmd[0] == "delete":
                editor.delete(cmd[1])
                print("Done")
            else:
                print("Unknown command")
        except NotImplementedError as e:
            print(str(e))
