import json
import os
import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

def main(event, context):
    """
    Main function, runs the atom parenthesing handling and the counting process for each substring containing an atom
    :param event: Input from the POST HTTP request received when the API is requested
    :param context: additional information that can be passed alongside the request body, not used here
    :return: an HTTP response with either a dictionnary result as the body or a readable error message
    """
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'):
        logger.info('Message received')
        string = event.get('body')

        # Most invalid molecule are flagged by the position brackets function so we filter them out here
        try:
            position_list = position_brackets(string)
        except TypeError as err:
            body = str(err)

            ERROR_RESPONSE = {
                "statusCode": 400,
                "body": json.dumps(body)
            }

            return ERROR_RESPONSE

        mult_array = apply_brackets(position_list, len(string))

        substring_list, index_list = split_atoms(string)
        logger.info(f'substring_list:{substring_list}')

        # Case of an empty substring, happens when there is no upper-case letter in the input
        if substring_list == ['']:
            body = 'There is no valid atom in your molecule, please mind your upper-cases!'

            ERROR_RESPONSE = {
                "statusCode": 400,
                "body": json.dumps(body)
            }

            return ERROR_RESPONSE

        else:
            dic = {}
            for i in range(len(substring_list)):
                count_atoms(substring_list[i], mult_array[index_list[i]], dic)

            body = {"message": "Function executed successfully!", "input": event, "result": dic}

            response = {
                    "statusCode": 200,
                    'headers': {'Content-Type': 'application/json'},
                    "body": json.dumps(body)
                }

            return response

    # Case of an empty input
    elif not event.get('body'):
        body = 'It looks like your molecule is empty, nature hates void so please enter something !'

        ERROR_RESPONSE = {
            "statusCode": 400,
            "body": json.dumps(body)
        }

        return ERROR_RESPONSE

    # For any other case that we might have missed
    else:
        ERROR_RESPONSE = {
            'statusCode': 400,
            'body': json.dumps('Oops, something went wrong!')
        }

        return ERROR_RESPONSE


def position_brackets(string):
    """
    Sub-function computing the position and multiplicative factor of all brackets
    :param string: Full molecule string
    :return: A list of positions and multiplicative factors or A TypeError with a readable error message if the molecule is invalid
    """
    brackets_dic = {')': '(',
                    ']': '[',
                    '}': '{'}

    length = len(string)

    list_opening_brackets = list(brackets_dic.values())
    list_closing_brackets = list(brackets_dic.keys())

    # screen for forbidden characters:
    for char in string:
        if (not char.isalnum()) & (char not in list_opening_brackets) & (char not in list_closing_brackets):
            raise TypeError(f'Unknown character {char} please enter a valid molecule!')

    stack = []
    res = []  # (opening pos, closing pos, number)
    for index in range(length):
        char = string[index]
        if char in list_opening_brackets:
            stack.append((char, index))
        elif char in list_closing_brackets:
            if stack:
                last_opened, last_opened_index = stack.pop()
            else:
                raise TypeError(f'Uncorrect parenthesing at {char} please enter a valid molecule!')

            if last_opened != brackets_dic[char]:
                raise TypeError(f'Uncorrect parenthesing at {char} please enter a valid molecule!')

            else:
                if index != length-1:
                    if string[index + 1].isdigit():
                        mult=int(string[index + 1])
                    elif string[index + 1].islower():
                        raise TypeError(f'Unexpected lowercase caracter at {string[index:index + 2]} please enter a valid molecule!')
                    else:
                        mult=1
                else:
                    mult=1

                res.append((last_opened_index, index, mult))

    if stack:
        still_opened, _ = stack.pop()
        raise TypeError(f'Parenthesis not closed at {still_opened} please enter a valid molecule!')
    return res


def apply_brackets(position_list, string_length):
    """
    Sub function computing an array that matches every position in the molecule string with the multiplicative factor
    resulting from the application of all parenthesis
    :param position_list: Output of position_brackets
    """
    res = [1] * string_length
    for start, end, mult in position_list:
        res[start:end] = [i * mult for i in res[start:end]]
    return res


def split_atoms(string):
    """
    Sub function splitting the full molecule string into substring each containing only one valid atom marked by an
    upper case letter
    :param string: Full molecule string
    :return: list of substrings and list of the starting index of these substrings to retrieve the multiplicative factor
    """
    tmp_str = ''
    index_list = []
    first_char = True
    for index in range(len(string)):
        char = string[index]
        if first_char:  # Remove caracters before first atom
            if char.isupper():
                first_char = False
                index_list.append(index)
                tmp_str += char

        else:
            if char.isupper():
                tmp_str += ';'
                index_list.append(index)
            tmp_str += char

    return tmp_str.split(';'), index_list


def count_atoms(string, mult, dic):
    """
    Sub function computing the atom present in a substring and its number based on the multiplicative factor from
    the parenthesis handling step
    :param string: Substring of the full molecule containing only one valid atom, necessary starting by an upper-case letter
    :param mult: Multiplicative factor coming from the parenthesis handling
    :param dic: Dictionary containing the composition of the molecule so far
    :return: None, only updates the dic argument
    """
    length = len(string)

    # Case of a one letter substring, it is an atom and it present only once
    if length == 1:
        atom = string[0]
        if atom in dic:
            dic[atom] += mult
        else:
            dic[atom] = mult

    # Otherwise the atom is made of the first letter + all subsequent lower-case letters so we run through those
    else:
        i = 1
        while (string[i].islower()) & (i<length-1):
            i+=1
        if string[i].islower(): # The string ends here
            atom = string
            if atom in dic:
                dic[atom] += mult
            else:
                dic[atom] = mult

        # The string is not finished yet, so we have to run through the number after the atom with the same approach
        else:
            atom = string[:i]
            next_i = i
            if length == next_i:
                if atom in dic:
                    dic[atom] += mult
                else:
                    dic[atom] = mult
            else: # If there is at least one digit we go through all subsequent ones
                if string[next_i].isdigit():
                    i = 0
                    while (string[next_i + i].isdigit()) & (next_i+i<length-1):
                        i+=1
                    if (next_i+i == length-1):
                        number = string[next_i]
                    else:
                        number = string[next_i:next_i+i]

                    if atom in dic:
                        dic[atom] += mult * int(number)
                    else:
                        dic[atom] = mult * int(number)
                else:
                    if atom in dic:
                        dic[atom] += mult
                    else:
                        dic[atom] = mult