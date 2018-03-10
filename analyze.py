#!/usr/bin/env: python3

# TODO: Build dictionary of collectors in order to classify 
#       transactions by type: bills, groceries, etc
#
#       Prompt user for classification type upon encounter
#       of unknown class


import re

money_pattern = re.compile('\d*[,]*\d+\.\d+')

#
# Creates a useful handle for where money goes to or comes from, called
# a collector. I'm assuming these collectors are unique so that I can 
# classify them as to what kind of transaction it is: bill, gas, etc.
#
def getCollectorString(line):
    result = ""
    for token in line:
        if len(token) > 0:
            result += token + " "

    return result.replace("\n", "")


#
# Helper function for making transaction list more concise. Returns
# index of collector if it's in the list, -1 otherwise.
#
def getIndex(arr, collector):
    index = 0
    for line in arr:
        if line[0] == collector:
            return index
        index += 1

    return -1


#
# Parses an input file until a specified stop point. Uses a regular
# expression to match a money line. Handles the special case for 
# USAA internal transactions and generic transactions given the
# file comes from USAA.
#
def getTransactions(f, stop_point):
    temp = []
    
    line = f.readline()
    while line:
        
        # Break at next section
        if line == stop_point:
            break
        
        tokens = line.split(" ")

        # Parse tokens looking for money pattern
        for token in tokens:
            if money_pattern.match(token):
                date = tokens[0]                      # date is first index
                money = float(token.replace(",", "")) # remove commas
                
                # USAA formats their statements so that internal transactions
                # only have one line. Consequently, if it's not an internal 
                # transaction, read next line to get collector. Otherwise, trim
                # up line appropriately.
                if "USAA" not in tokens:
                    line = f.readline()
                    tokens = line.split(" ")

                else:
                    tokens = tokens[10:]

                new_line = [getCollectorString(tokens), date, money]
                temp.append(new_line)


        line = f.readline()
    
    # Now that we've built a list of transactions, make the list more 
    # concise by combining common collectors. Do this by appending dates
    # and incrementing total money spent or deposited.
    transactions = []
    for transaction in temp:
        index = getIndex(transactions, transaction[0])

        if index != -1:
            transactions[index][1] += ", " + transaction[1] # append dates
            transactions[index][2] += transaction[2]        # increment total
        else:
            transactions.append(transaction)
            

    return transactions 


def getClassifiers(file_name):
    classifiers = {}

    with open(file_name, "r") as f:
        line = f.readline()

        while line:
            tokens = line.split(", ")
#            print(tokens[0])
#            print(tokens[1].replace("\n", ""))
            # first index is collector
            # second is class
            classifiers[tokens[0]] = tokens[1].replace("\n", "")
#            print(str(classifiers))
#            k = input()

            line = f.readline()

    return classifiers


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
   
    classifiers = getClassifiers("collectors")
    print(str(classifiers.values()))


main()
