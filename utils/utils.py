def read_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            return [line for line in lines if line]
    except FileNotFoundError:
        return []

def remove_from_list_file(filename, item):
    try:
        existing_items = read_list_from_file(filename)
        updated_items = [existing for existing in existing_items if existing != item]
        with open(filename, 'w', encoding='utf-8') as file:
            for updated_item in updated_items:
                file.write(f"{updated_item}\n")
    except Exception as e:
        print(f"Error removing item from list: {e}")
