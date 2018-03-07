#!/usr/bin/env: python3

import re

money_pattern = re.compile('\d*[,]*\d+\.\d+')

def getCollectorString(line):
    result = ""
    for token in line:
        if len(token) > 0:
            result += token + " "

    return result.replace("\n", "")

# TODO: Only call this function if in deposits/debits
#       Endless loop on prelude
def getTransferType(line):
    print(len(line))
    print(str(line))

    result = ""
    index = 0

    while 1:
        print(line[index])
        if money_pattern.match(line[index]):
            break

        index += 1

    while line[index] != "":
        result += str(line[index]) + " "

    return result
        
def contains(arr, collector):
    index = -1
    for line in arr:
        if arr[0] == collector:
            return index
        index += 1

    return index



f = open("20180216_raw", "r")

#money_pattern = re.compile('\d*[,]*\d+\.\d+')
money = 0.0
date = ""
found_money = False
ledger = []

# Deposit/Debit type immediately follows amount
# Date is first index
# Internal funds transfers have no additional line

for line in f:
    # Marks end of file, no more debits after this
    if line == " ACCOUNT BALANCE SUMMARY\n":
        print("--- Account balance summary --- ")
    elif line == "    DEPOSITS AND OTHER CREDITS\n":
        print("--- Deposits and other credits ---")
    elif line == "    OTHER DEBITS\n":
        print("--- Other Debits --- ")
    temp = line.split(" ")

    # if money is found, next line is where money was spent
    if found_money:
        collector = getCollectorString(temp)
        new_line = [getCollectorString(temp), date, money]
        index = contains(ledger, collector)

        # TODO
        # Check if ledger contains collector
        # If ledger already has collector, increment money and add date
        # Otherwise, add new collector
        if index == -1:
            ledger.append([collector, date, money])
            print(str(new_line))
        else:
            ledger[index][1] += ", " + date
            ledger[index][2] += money
            print(str(ledger[index]))
            
#        ledger.append(new_line)
        found_money = False
        k = input()

    for token in temp:
        if money_pattern.match(token):
            # Date is first index
            date = temp[0]
            
            if "\n" in token: # remove new line escapes
                token = token[:-1]
            money = float(token.replace(",", "")) # remove commas
            found_money = True

print(monies)

