
def escapeId(id):
    """ Remove forbidden characters from id """
    return id.replace("-", "_")

def indent(level):
    """Generate indentation"""
    return " " * 4 * level

def digraphHeader(file, indentLevel=0):
    """ Print digraph header into given file """
    file.write(indent(indentLevel) + "digraph {\n")

def endGraph(file, indentLevel=0):
    """ End graph """
    file.write(indent(indentLevel) + "}\n")

def fromMm(mm):
    return int(mm / 25.4 * 72)