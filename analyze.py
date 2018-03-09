#!/usr/bin/env: python3

import re

money_pattern = re.compile('\d*[,]*\d+\.\d+')


def getCollectorString(line):
    result = ""
    for token in line:
        if len(token) > 0:
            result += token + " "

    return result.replace("\n", "")


# TODO: Combine transactions to make the list more concise
def getTransactions(f, stop_point):
    money = 0.0
    date = ""
    found_money = False
    temp = []
    
    line = f.readline()
    
    while line:
        
        # Break at next section
        if line == stop_point:
            break
        
        tokens = line.split(" ")

        # If money is found, next line is where money was spent
        if found_money:
            new_line = [getCollectorString(tokens), date, money]
            temp.append(new_line)

            # Reset boolean so we can keep iterating
            found_money = False

        for token in tokens:
            if money_pattern.match(token):
                date = tokens[0] # date is first index
                money = float(token.replace(",", "")) # remove commas
                # Now that we've found money, we need to get the 
                # collector from the next line
                found_money = True
        

        line = f.readline()

    print(len(temp))
    transactions = []
    for transaction in temp:
        index = contains(transactions, transaction[0])

        if index != -1:
            transactions[index][2] += transaction[2]
            transactions[index][1] += transaction[1]
        else:
            transactions.append(transaction)
            

    return transactions 

   
# TODO: Decide how to parse summary lines
def getSummary(f):
    date = ""
    money = ""

    line = f.readline()
    while line:
        temp = line.split(" ")
      
        k = input()
        line = f.readline()


def contains(arr, collector):
    index = 0
    for line in arr:
        if line[0] == collector:
            return index
        index += 1

    return -1


def main():
    #" ACCOUNT BALANCE SUMMARY\n":

    with open("20180216_raw", "r") as f:
        line = f.readline()
       
        # Skip information I don't know how to handle yet
        while line:
            if line == "    DEPOSITS AND OTHER CREDITS\n":
                break
            line = f.readline()
                
        deposits = getTransactions(f, "    OTHER DEBITS\n")
        debits = getTransactions(f, " ACCOUNT BALANCE SUMMARY\n")

    print(len(debits))

main()
