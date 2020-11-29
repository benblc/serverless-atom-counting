import json
import os
import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}

ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}

def main(event, context):
    """
    Runs the atom couting process
    :param event:
    :param context:
    :return:
    """
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'):
        logger.info('Message received')

        string = event.get('body')

        position_list = position_brackets(string)
        mult_array = apply_brackets(position_list, len(string))

        substring_list, index_list = split_atoms(string)

        dic = {}

        for i in range(len(substring_list)):
            count_atoms(substring_list[i], mult_array[index_list[i]], dic)

        body = {"message": "Your function executed successfully!", "input": event, "result": dic}

        response = {
                "statusCode": 200,
                "body": json.dumps(body)
            }

        return response

    else:
        return ERROR_RESPONSE



#
# def main(string):
#     position_list = position_brackets(string)
#     mult_array = apply_brackets(position_list, len(string))
#
#     substring_list, index_list = split_atoms(string)
#
#     dic = {}
#
#     for i in range(len(substring_list)):
#         count_atoms(substring_list[i], mult_array[index_list[i]], dic)
#
#     return dic


def position_brackets(string):
    brackets_dic = {')': '(',
                    ']': '[',
                    '}': '{'}

    list_opening_brackets = list(brackets_dic.values())
    list_closing_brackets = list(brackets_dic.keys())

    # screen for forbidden characters:
    for char in string:
        if (not char.isalnum()) & (char not in list_opening_brackets) & (char not in list_closing_brackets):
            raise TypeError(f'Unknown character {char}')

    stack = []
    res = []  # (opening pos, closing pos, number)
    for index in range(len(string)):
        char = string[index]
        if char in list_opening_brackets:
            stack.append((char, index))
        elif char in list_closing_brackets:
            last_opened, last_opened_index = stack.pop()
            if last_opened != brackets_dic[char]:
                raise TypeError(f'Uncorrect parenthesing at {char}')
            else:
                if string[index + 1].isdigit():
                    mult = int(string[index + 1])
                elif string[index + 1].islower():
                    raise TypeError(f'Unexpected lowercase caracter at {string[index:index + 2]}')
                else:
                    mult = 1

                res.append((last_opened_index, index, mult))

    return res


def apply_brackets(position_list, string_length):
    res = [1] * string_length
    for start, end, mult in position_list:
        res[start:end] = [i * mult for i in res[start:end]]
    return res


def split_atoms(string):
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
    length = len(string)

    if length == 1:
        atom = string[0]
        if atom in dic:
            dic[atom] += mult
        else:
            dic[atom] = mult

    else:
        if string[1].islower():
            if string[2].islower():
                atom = string[0:3]
                next_i = 3
            else:
                atom = string[0:2]
                next_i = 2
        else:
            atom = string[0]
            next_i = 1

        if string[next_i].isdigit():
            if atom in dic:
                dic[atom] += mult * int(string[next_i])
            else:
                dic[atom] = mult * int(string[next_i])
        else:
            if atom in dic:
                dic[atom] += mult
            else:
                dic[atom] = mult