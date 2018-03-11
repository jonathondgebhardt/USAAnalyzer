#!/usr/bin/env: python3

# TODO: Prompt user for classification type upon encounter
#       of unknown class.
#
#       If a refund is received, there's no differentiation between
#       the purchase and the refund. Maybe getting transaction type
#       is useful.
#

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


#
# Builds dictionary of known classification types from argument file. Arrangement
# is "Collector Handle": "Classification". Returns the list.
#
def getClassifiers(file_name):
    classifiers = {}

    with open(file_name, "r") as f:
        line = f.readline()

        while line:
            # first index is collector, second is class
            tokens = line.split(", ")
            classifiers[tokens[0]] = tokens[1].replace("\n", "")

            line = f.readline()

    return classifiers


#
# Builds a list of money spent on classifcation type. Returns 
# the list, deposit total, debit total.
#
def getPortions(deposits, debits, classifiers):
    temp = []
    debit_total, deposit_total = 0.0, 0.0

    # Prefill temp with known classes and initial money value. 
    # These are retrieved from the value position in the dictionary.
    for k, v in classifiers.items():
        new_line = [v, 0.0]
        if new_line not in temp:
            temp.append(new_line)


    # Iterate list incremementing appropriate class total
    # TODO: Prompt user if unknown class is found
    for transaction in deposits:
        for record in temp:
            if record[0] == classifiers.get(transaction[0]):
                record[1] += transaction[2] # increment money
                deposit_total += transaction[2]

    for transaction in debits:
        for record in temp:
            if record[0] == classifiers.get(transaction[0]):
                record[1] += transaction[2] # increment money
                debit_total += transaction[2]

    return temp, deposit_total, debit_total 


def main():
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
    portions, deposit_total, debit_total = getPortions(deposits, debits, classifiers)
    val_total = 0.0
    for line in portions:
        val = 0.0

        if line[0] == "deposit":
            val = line[1] / deposit_total
        else:
            val = line[1] / debit_total
            val_total += val

        print("{}:\n{:10.2f} -- {:.2%}".format(line[0], line[1], val)) 



main()
