import yaml


class Namespace(object):

    def __init__(self, *args, sub_space=None, **kwargs):
        self.add(*args, **kwargs, sub_space=sub_space)

    def __str__(self):
        return "\n".join(self.__print())

    def __len__(self):
        return len(self.__dict__)

    def add(self, *args, sub_space=None, kwargs_first=False, **kwargs):
        if sub_space is None:
            sub_space = []
        if isinstance(sub_space, str):
            sub_space = [sub_space]
        if sub_space:
            try:
                self.__dict__[sub_space[0]].add(*args, sub_space=sub_space[1:], **kwargs)
            except KeyError:
                self.add({sub_space[0]: Namespace(*args, sub_space=sub_space[1:], **kwargs)})
        else:
            if kwargs_first:
                self.__add_dict(kwargs, sub_space=sub_space)
                self.__add_args(args, sub_space=sub_space)
            else:
                self.__add_args(args, sub_space=sub_space)
                self.__add_dict(kwargs, sub_space=sub_space)

    def remove(self, keys):
        if not isinstance(keys, list):
            keys = [keys]
        for key in keys:
            del self.__dict__[key]

    def print(self, head=None, tab="  ",):
        print("\n".join(self.__print(head=head, tab=tab)))

    def save(self, filepath, header=None, tab="  "):
        with open(filepath, "w") as file:
            for line in header:
                file.write("# %s\n" % line)
            for line in self.__print(tab=tab):
                file.write("%s\n" % line)
        file.close()

    def append(self, *args, **kwargs):
        self.__append_dict(kwargs)
        for arg in args:
            self.__append_dict(arg)

    def get(self, sub_space=None):
        if sub_space is None:
            sub_space = []
        if not isinstance(sub_space, list):
            sub_space = [sub_space]
        if sub_space:
            if len(sub_space) == 1:
                return self.__dict__[sub_space[0]]
            else:
                return self.__dict__[sub_space[0]].get(sub_space[1:])
        else:
            return self.__dict__

    def delete(self, key, recursive=True, parent=None):
        to_delete = []
        for name, item in self.__dict__.items():
            if isinstance(item, Namespace) and "NAME" in item.__dict__ and key == item.NAME:
                to_delete.append(name)
        for name in to_delete:
            del self.__dict__[name]
            print("%s node deleted from %s" % (key, parent))
        if recursive:
            for _, item in self.__dict__.items():
                if isinstance(item, Namespace) and "CHILDREN" in item.__dict__:
                    item.CHILDREN.delete(key, recursive=True, parent=item.NAME)

    def write(self, file_path, tab_size=2, tabs=0):
        for name, data in self.__dict__.items():
            if name.startswith("NODE"):
                with open(file_path, "a") as file:
                    if data.COMMENT is None:
                        file.write("%s%s {\n" % (" " * tabs * tab_size, data.NAME))
                    else:
                        file.write("%s%s { # %s\n" % (" " * tabs * tab_size, data.NAME, data.COMMENT))
                data.CHILDREN.write(file_path, tab_size=tab_size, tabs=tabs+1)
                with open(file_path, "a") as file:
                    file.write("%s}\n" % (" " * tabs * tab_size))
            else:
                with open(file_path, "a") as file:
                    if isinstance(data, list):
                        if len(data) == 1:
                            file.write("%s%s [ %s ]\n" % (" " * tabs * tab_size, name, data[0]))
                        else:
                            file.write(
                                "%s%s [\n%s\n%s]\n" % (
                                    " " * tabs * tab_size,
                                    name,
                                    "\n".join(["%s%s" % (" " * tab_size * (tabs + 1), item) for item in data]),
                                    " " * tabs * tab_size
                                )
                            )
                    else:
                        file.write("%s%s %s\n" % (" " * tabs * tab_size, name, data))

    def __write_node(self):
        pass

    def __append_dict(self, dictionary):
        for key, item in dictionary.items():
            try:
                self.__dict__[key].append(item)
            except KeyError:
                self.__dict__[key] = [item]

    def __add_args(self, args, sub_space):
        for arg in args:
            if isinstance(arg, str):
                with open(arg, "r") as file:
                    arg = yaml.load(file)
            self.__add_dict(arg, sub_space=sub_space)

    def __add_dict(self, dictionary, sub_space):
        for key, item in dictionary.items():
            if isinstance(item, dict):
                self.add({key: Namespace(item)}, sub_space=sub_space)
            else:
                self.__dict__.update({key: item})

    def __print(self, head=None, tab="  ", level=0):
        lines = []
        for key, item in self.__dict__.items():
            if isinstance(item, Namespace):
                lines.append("%s%s:" % (tab * level, key))
                lines += item.__print(tab=tab, level=level+1)
            else:
                if isinstance(item, str):
                    lines.append("%s%s: '%s'" % (tab * level, key, item))
                else:
                    lines.append("%s%s: %s" % (tab * level, key, item))
            if head is not None and len(lines) > head:
                break
        return lines

    def get_nodes(self):
        nodes = []
        for name, node in vars(self).items():
            if name.startswith("NODE"):
                if node.NAME.startswith("DEF"):
                    nodes.append(node.NAME.split(" ")[1])
                nodes += node.CHILDREN.get_nodes()
        return nodes

    def apply_nodes(self, new_nodes):
        # For each data node
        for parent_name, parent in vars(self).items():
            # Check the node name is in the new_nodes yaml file
            if parent_name.startswith("NODE") and \
                    parent.NAME.startswith("DEF") and \
                    parent.NAME.split(" ")[1] in vars(new_nodes):
                parent_node_name = parent.NAME.split(" ")[1]
                print("%s:" % parent_node_name)
                # For each new node to be applied to the parent_node
                for new_node_name, new_node in new_nodes.get(parent_node_name).get().items():
                    # Check if the new node already exists as a child
                    already_exists = False
                    for child_name, child_node in vars(parent.CHILDREN).items():
                        if child_name.startswith("NODE") and child_node.NAME == new_node_name:
                            for field_name, field_value in new_node.get().items():
                                # If the field already exists
                                if field_name in child_node.CHILDREN.get():
                                    print("\t%s:" % new_node_name)
                                    already_exists = True
                                    # If the field value is already correct
                                    if child_node.CHILDREN.get(field_name) == field_value:
                                        print(
                                            "\t\tNot changing %s field with value: %s" % (
                                                field_name, field_value
                                            )
                                        )
                                    else:
                                        child_node.CHILDREN.get()[field_name] = field_value
                                        print(
                                            "\t\tChanging %s field value from %s to %s" % (
                                                field_name, child_node.CHILDREN.get(field_name), field_value
                                            )
                                        )
                                else:
                                    child_node.CHILDREN.get()[field_name] = field_value
                                    print(
                                        "\t\tAdded new field %s with value %s" %
                                        (field_name, field_value)
                                    )
                    if not already_exists:
                        print("\tAdded new node %s:" % new_node_name)
                        for field_name, field_value in new_node.get().items():
                            print(
                                "\t\t%s: %s" %
                                (field_name, field_value)
                            )
                        n = 0
                        while True:
                            name = "NODE_%i" % n
                            if name in parent.CHILDREN.get():
                                n += 1
                            else:
                                break
                        children = parent.CHILDREN
                        parent.CHILDREN = Namespace(
                            {
                                name: {
                                    "NAME": new_node_name,
                                    "COMMENT": None,
                                    "CHILDREN": new_node.get()
                                }
                            },
                            children.get()
                        )

            if parent_name.startswith("NODE"):
                parent.CHILDREN.apply_nodes(new_nodes)


if __name__ == "__main__":

    namespace = Namespace(a=1, b=2, c=3, d={"e": 5, "f": 6}, g={"h": 8, "i": {"j": 10}}, k=11)
    print(namespace)
    print("---")
    print(namespace.get(["d", "e"]))
    print("---")
    namespace.add({"l": 12}, sub_space=["g", "i"])
    print(namespace)

