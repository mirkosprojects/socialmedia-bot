def compare_jsons(template, data, errors = []):
    """compares if keys from template are in data, returns non existing keys"""
    if type(template) == dict:
        for key, item in template.items():
            if key in data:
                compare_jsons(item, data[key], errors)
            else:
                errors.append(key)
    return(errors)