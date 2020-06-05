from crispy_forms.layout import HTML

def jsonDiffEditor(field, json):
    return HTML(f"""
        <div class="w-full my-4" id="jsoneditor"></div>
        <link href="/static/css/jsoneditor.min.css" rel="stylesheet" type="text/css">
        <style>
            .different_element {{
                background-color: #acee61;
            }}
            .different_element div.jsoneditor-field,
            .different_element div.jsoneditor-value {{
                color: red;
            }}
            .jsoneditor {{
                border: none;
            }}
        </style>
        <script src="/static/js/jsoneditor.min.js"></script>
        <script>
            const originalJson = {json};
            var initialJson = {json};
            var resultInput = document.getElementById("{field.id_for_label}");

            function findNodeInJson(json, path) {{
                if(!json || path.length ===0) {{
                    return {{field: undefined, value: undefined}}
                }}
                const first = path[0]
                const remainingPath = path.slice(1)

                if(remainingPath.length === 0) {{
                    return {{ field: (typeof json[first] !== 'undefined' ? first : undefined), value: json[first] }}
                }} else {{
                    return findNodeInJson(json[first], remainingPath)
                }}
            }}

            function flattenRec(o, root, result) {{
                if (!(o.constructor == Object)) {{
                    result[root] = o;
                    return;
                }}
                Object.keys(o).forEach( key => {{
                    var delimiter = root.length != 0 ? "." : "";
                    flattenRec(o[key], root + delimiter + key, result);
                }});
            }}

            function flatten(o) {{
                result = [];
                flattenRec(o, "", result);
                return result;
            }}

            function mergeArrays(...arrays) {{
                let jointArray = []

                arrays.forEach(array => {{
                    jointArray = [...jointArray, ...array]
                }})
                const uniqueArray = jointArray.reduce((newArray, item) => {{
                    if (newArray.includes(item)) {{
                        return newArray
                    }} else {{
                        return [...newArray, item]
                    }}
                }}, [])
                return uniqueArray
            }}

            function jsonDiff(newJson, originalJson) {{
                var newJ = flatten(newJson);
                var origJ = flatten(originalJson);
                var add = {{}};
                var remove = {{}};
                var change = {{}};
                mergeArrays(Object.keys(newJ), Object.keys(origJ)).forEach( key => {{
                    if (!(key in newJ)) {{
                        remove[key] = origJ[key];
                    }}
                    else if (!(key in origJ)) {{
                        add[key] = newJ[key];
                    }}
                    else if (newJ[key] != origJ[key]) {{
                        if (Array.isArray(newJ[key])) {{
                            var newArr = newJ[key];
                            var origArr = origJ[key]
                            toAdd = newArr.filter((x) => !origArr.some((y) => x == y));
                            toRemove = origArr.filter((x) => !newArr.some((y) => x == y));
                            if (toAdd.length != 0) {{
                                add[key] = toAdd;
                            }}
                            if (toRemove.length != 0) {{
                                remove[key] = toRemove;
                            }}
                        }}
                        else {{
                            change[key] = newJ[key];
                        }}
                    }}
                }});

                return {{
                    "add": add,
                    "remove": remove,
                    "change": change
                }}
            }}

            function onClassName({{ path, field, value }} ) {{
                const thisNode = findNodeInJson(initialJson, path)
                const oppositeNode = findNodeInJson(originalJson, path)
                let isValueEqual = JSON.stringify(thisNode.value) === JSON.stringify(oppositeNode.value)

                if(Array.isArray(thisNode.value) && Array.isArray(oppositeNode.value)) {{
                    isValueEqual = thisNode.value.every(function (e) {{
                        return oppositeNode.value.includes(e)
                    }})
                }}

                if (thisNode.field === oppositeNode.field && isValueEqual) {{
                    return 'the_same_element'
                }} else {{
                    return 'different_element'
                }}
            }}

            var editor;
            const container = document.getElementById("jsoneditor");
            const options = {{
                onClassName: onClassName,
                onChangeJSON: function (j) {{
                    initialJson = j;
                    resultInput.value = JSON.stringify(jsonDiff(j, originalJson));
                    editor.refresh();
                    console.log(jsonDiff(j, originalJson));
                }}
            }};
            editor = new JSONEditor(container, options);

            // set json
            editor.set(initialJson);

            // get json
            const updatedJson = editor.get();
        </script>
    """)