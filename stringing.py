import pandas as pd
import re
import os

conductors = [
    '795 KCMIL 37 STRAND AAC "ARBUTUS"', '336.4 KCMIL 19 STRAND AAC "TULIP"',
    '1272.0 KCMIL 61 STRAND AAC "NARCISSUS"'
]
loading_zones = ['NESC MEDIUM LOAD ZONE', 'SPECIAL_LOAD_ZONE']
design_conditions = [
    '@ 15F, 0.25 IN ICE, 4.0 LB/FT^2 WIND, INITIAL',
    '@ 0F, 0.0 IN ICE, 0.0 LB/FT^2 WIND, INITIAL',
    '@ 15F, 0.0 IN ICE, 0.0 LB/FT^2 WIND, FINAL',
    '@ 15F, 0.0 IN ICE, 0.0 LB/FT^2 WIND, INITIAL'
]

sag_text = 'SAG FT-IN'
four_digit_sag_value = False

span_lengths_special_text = """
Specify span lengths values separated by commas or
select .txt file with one span length value per line.
"""

print_order = [
    'conductor',
    'ruling_span',
    'load_zone_max_tension',
    'design_tension_condition',
    'tension_values',
    'temp_values',
    'sag_label',
    'sag_table',
    'closing'
    ]  


def length_of_longest_string(d: dict):
    d_new = {k: v for k, v in d.items() if k != 'sag_table'}
    max_length = 0
    for value in d_new.values():
        if isinstance(value, str):
            # Calculate length including expanded tabs (assuming tab size of 8)
            expanded_length = len(value.expandtabs())
            if expanded_length > max_length:
                max_length = expanded_length
    if four_digit_sag_value:
        max_length += 1
    return max_length 

def get_span_values():
    while True:
        try:
            choice = input(
                f'Span Length\n1. Enter span lengths manually\n2. Import from text file\n')
            if int(choice) == 1:
                values = input('Enter span values separated by commas: ')
                return [int(item.strip()) for item in values.split(',')]
            elif int(choice) == 2:
                instructions = 'Select the text file with span values. One value per line.'
                filename = select_by_file_type(
                    file_type='.txt', special_instructions=instructions)
                return read_numerical_text_file(filename)
            else:
                print('Invalid choice. Please enter try again.')
        except ValueError:
            print('Invalid Input. Please enter a valid choice.')


def read_numerical_text_file(filename):
    numbers = []
    with open(filename, 'r') as f:
        for line in f:
            value = line.strip()
            if value:
                numbers.append(int(value))
    return numbers


def select_by_file_type(directory='.', file_type='', special_instructions=''):
    print(f'')
    # List all XML files in the directory
    xml_files = [f for f in os.listdir(
        directory) if f.lower().endswith(file_type)]

    if not xml_files:
        print(f'No {file_type} files found in the directory.')
        return None

    # Display the list of XML files
    print(f"Available {file_type} files:")
    for idx, file in enumerate(xml_files, start=1):
        print(f"{idx}. {file}")

    # Prompt user to select a file
    while True:
        try:
            choice = int(input("Enter the number of the file to process: "))
            if 1 <= choice <= len(xml_files):
                selected_file = xml_files[choice - 1]
                print(f"Selected file: {selected_file}\n")
                return selected_file
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def process_xml_file(filename, span_values=''):
    df = pd.read_xml(filename, xpath='//table/*')
    ruling_span = df['ruling_span'].iloc[0]
    filter_values = span_values
    if len(filter_values) != 0:
        df = df[df['span_length'].isin(filter_values)]
    df = df.round({'horz_tension': 0, 'span_length': 0, 'temp': 0})
    df['span'] = 'ft-in'
    df[['horz_tension', 'span_length', 'temp']] = df[[
        'horz_tension', 'span_length', 'temp']].astype(int)
    table = df.pivot_table(values='mid_span_sag', index='span_length', columns=[
                           'horz_tension', 'temp', 'span'], sort=False)
    table = table.applymap(feet_to_inches)
    return [table, ruling_span]


def format_line(left_text, right_text, total_width):
    space = total_width - len(left_text) - len(right_text)
    if space < 0:
        raise ValueError("Total width is too small for the given texts.")
    return f"{left_text}{' ' * space}{right_text}\n"


def get_numerical_input(text_input: str):
    while True:
        user_input = input(f'Please input {text_input}: ')
        try:
            number = int(user_input)
            return number
        except ValueError:
            print(' Invalid input. Please enter numerical value')


def feet_to_inches(decimal_value) -> str:
    feet = int(decimal_value)
    partial_feet = decimal_value - feet
    inches = round(partial_feet * 12)
    if inches == 12:
        feet += 1
        inches = 0
    return text_output_feet_to_inches(feet, inches)


def text_output_feet_to_inches(feet, inches):
    if feet == 0:
        return f'0-{inches}'
    elif inches == 0:
        return f'{feet}-0'
    else:
        return f'{feet}-{inches}'


def check_span_temps(temps: list):
    expected_temps = [i for i in range(30, 100, 10)]
    for temp in temps:
        if temp not in expected_temps:
            raise ValueError(f'Temp {temp} not in expected value range')


def select_from_list(items: list, selection: str = 'item'):
    if not items:
        print("The list is empty.")
        return None

    print(f'Please select a {selection}')
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item}")

    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(items):
                return items[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def separate_table_values(table_data: pd.DataFrame) -> tuple:
    table_as_string = table_data[0].to_string()
    selected_span_values = {}
    for line in table_as_string.splitlines():
        if 'tension' in line:
            values = re.findall(r'\d+', line)
            tension_values = list(map(int, values))
        elif 'temp' in line:
            find_values = re.findall(r'\d+', line)
            temp_values = list(map(int, find_values))
            check_span_temps(temp_values)
        elif 'span_length' in line or 'ft-in' in line:
            continue
        else:
            first_number = re.search(r'\b\d+\b', line)
            sag_values = re.findall(r'\b\d+-\d+\b', line)
            if first_number:
                selected_span_values[int(
                    first_number.group())] = list(sag_values)

    return {
        'tension_values': tension_values,
        'first_number': first_number,
        'selected_span_values': selected_span_values,
        'temp_values': temp_values
    }


def string_with_tab(header='', values=[], extra_indent=False):
    output_string = ''
    output_string += f'{header}'
    for value in values:
        if value == values[len(values)-1]:
            output_string += f'{value}'
        else:
            output_string += f'{value}\t'
    return output_string


def span_string(selected_span_values) -> str:
    output = '\n'
    for span in selected_span_values:
        output += f'{span}\t\t'
        n = len(selected_span_values[span])
        for index, value in enumerate(selected_span_values[span]):
            if selected_span_values[span][n-1] and len(value) == 4:
                four_digit_sag_value = True
            if index + 1 == len(selected_span_values[span]):
                output += f'{value}'
            else:
                output += f'{value}\t'
        output += '\n'
    return output

def write_to_file(text_dict, print_order, default_filename='stringing_table.txt'):
    # Get filename from user or use default
    user_input = input(f"Enter output filename (default: {default_filename}): ").strip()
    filename = user_input if user_input else default_filename
    
    # Split filename into name and extension
    base_name, ext = os.path.splitext(filename)
    if not ext:
        ext = ".txt"
    
    # Initialize counter for filename increment
    counter = 0
    final_filename = f"{base_name}{ext}"
    
    # Check if file exists and increment if necessary
    while os.path.exists(final_filename):
        counter += 1
        final_filename = f"{base_name}_{counter}{ext}"
    
    print(f'Writing file: {final_filename}')
    
    # Write strings to file
    try:
        with open(final_filename, 'w', encoding='utf-8') as f:
            for item in print_order:
                f.write(text_dict[item].expandtabs())
        return final_filename
    except Exception as e:
        raise Exception(f"Error writing to file {final_filename}: {str(e)}")


def main():
    # Text dictionary to gather all text elements, print order determined by print_order variable
    text_dict = {}

    # select xml file to process
    xml_file = select_by_file_type(file_type='.xml')

    # input span values
    selected_span_values = get_span_values()

    # read and process xml file
    table_data = process_xml_file(xml_file, span_values=selected_span_values)

    # select conductor
    conductor = select_from_list(conductors, 'conductor')
    text_dict['conductor'] = f'CONDUCTOR: {conductor}\n'

    # enter tension values
    max_tension = get_numerical_input('max tension')
    design_tension = get_numerical_input('design tension')

    # enter load zone
    load_zone = select_from_list(loading_zones, 'load zone')

    # enter design condition
    design_condition = select_from_list(design_conditions, 'design condition')
    text_dict['design_tension_condition'] = f'DESIGN: {design_tension} LB {design_condition}\n\n'

    # convert Dataframe table values to table dict
    table_data_dict = separate_table_values(table_data)

    # text values for final table
    tension_values = table_data_dict['tension_values']
    text_dict['tension_values'] = string_with_tab(header='TENSION (LB)\t', values=tension_values)
    
    temp_values = table_data_dict['temp_values']
    text_dict['temp_values'] = string_with_tab(header='\nTEMP (F)\t', values=temp_values)

    selected_span_values = table_data_dict['selected_span_values']
    text_dict['sag_table'] = span_string(selected_span_values)

    # get length of longest string to set table spacing 
    longest_line_int = length_of_longest_string(text_dict)

    # get text for lines with variable line spacing, use longest line length 
    text_dict['sag_label'] = f'\n{sag_text.center(longest_line_int,"-")}'
    text_dict['ruling_span'] = format_line(f'RULING SPAN (FT): {table_data[1]}', 'STRING TABLE USING INITIAL SAG', longest_line_int)
    text_dict['load_zone_max_tension'] = format_line(load_zone, f'MAX TENSION = {max_tension} LB', longest_line_int)
    text_dict['closing'] = longest_line_int * '-'

    # write to file
    write_to_file(text_dict, print_order)

    # output to console
    for item in print_order:
        print(text_dict[item], end="")

if __name__ == '__main__':
    main()
