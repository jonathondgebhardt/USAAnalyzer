#!/usr/bin/env: python3

import re

money_pattern = re.compile('\d*[,]*\d+\.\d+')
deposits = []
debits = []

def getCollectorString(line):
    result = ""
    for token in line:
        if len(token) > 0:
            result += token + " "

    return result.replace("\n", "")


def getDeposits(f):
    money = 0.0
    date = ""
    found_money = False
    
    line = f.readline()
    
    while line:
        
        # Break at next section
        if line == "    OTHER DEBITS\n":
            break
        
        # Deposit/Debit type immediately follows amount
        # Date is first index
        # Internal funds transfers have no additional line
        temp = line.split(" ")

        # if money is found, next line is where money was spent
        if found_money:
            collector = getCollectorString(temp)
            new_line = [getCollectorString(temp), date, money]
            deposits.append(new_line)
            found_money = False

        for token in temp:
            if money_pattern.match(token):
                # Date is first index
                date = temp[0]
                money = float(token.replace(",", "")) # remove commas
                found_money = True
        

        line = f.readline()
    
    print(len(deposits))


def getDebits(f):
    money = 0.0
    date = ""
    found_money = False
    
    line = f.readline()
    
    while line:
        
        # Break at next section
        if line == " ACCOUNT BALANCE SUMMARY\n":
            break
        
        # Deposit/Debit type immediately follows amount
        # Date is first index
        # Internal funds transfers have no additional line
        temp = line.split(" ")

        # if money is found, next line is where money was spent
        if found_money:
            collector = getCollectorString(temp)
            new_line = [getCollectorString(temp), date, money]
            debits.append(new_line)
            found_money = False

        for token in temp:
            if money_pattern.match(token):
                # Date is first index
                date = temp[0]
                money = float(token.replace(",", "")) # remove commas
                found_money = True
        

        line = f.readline()
    
    print(len(debits))


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

def main():
    #" ACCOUNT BALANCE SUMMARY\n":

    with open("20180216_raw", "r") as f:
        line = f.readline()
        
        while line:
            if line == "    DEPOSITS AND OTHER CREDITS\n":
                break
            line = f.readline()
                
        getDeposits(f)
        getDebits(f)


main()
