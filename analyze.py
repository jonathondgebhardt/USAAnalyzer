#!/usr/bin/env: python3

""" 
    A user interaction based python script that analyzes a USAA bank statement. There
    are plans to add visual representations of how money is spent and ultimately 
    compare the new bank statement to past statements. 
    
    This script has some drawbacks:
        - If a refund is credited back using the same name, it might get marked
        as a deposit and a debit with some weird side effects.
        - Classifying transactions is a little crude: I would like to allow the 
        user to get more information about at transaction if they'd like. This 
        can probably be fixed by representing data differently.

    """


#
# TODO: Prompt user for classification type upon encounter
#       of unknown class.
#
#       If a refund is received, there's no differentiation between
#       the purchase and the refund. Maybe getting transaction type
#       is useful.
#
#       Output a file containing collectors if file doesn't already
#       exist.
#

import re
import os.path
import argparse


money_pattern = re.compile('\d*[,]*\d+\.\d+')
collector_types = {1: "deposit", 2: "misc", 3: "grocery", 4: "restaurant", 5: "bill", 6: "coffee", 7: "saving"}


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

    return result.strip()


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
# is "Collector Handle": "Classification". Returns the dictionary.
#
def getClassifiers(collectors):
    classifiers = {}

    for line in collectors:
        # first index is collector, second is class
        classifiers[line[0]] = line[1].strip()


    return classifiers


#
# Builds a list of money spent on classifcation type. Returns 
# the list, deposit total, debit total.
#
def getPortions(deposits, debits, classifiers):
    temp = []
    debit_total, deposit_total = 0.0, 0.0

    # Prefill temp with known class types and initial money value. 
    # Class types are retrieved from the value position in the dictionary.
    for k, v in classifiers.items():
        new_line = [v, 0.0]
        if new_line not in temp:
            temp.append(new_line)


    # Iterate list incremementing appropriate class total
    for transaction in deposits:
        temp[0][1] += transaction[2] 
        deposit_total += transaction[2]

    for transaction in debits:
        for record in temp:
            if record[0] == classifiers.get(transaction[0]):
                record[1] += transaction[2] # increment money
                debit_total += transaction[2]


    return temp, deposit_total, debit_total 



# 
# TODO: Also show user when they made transaction and for how much?
#
# Builds a file of collectors and class types. This file is stored
# in the working directory and should be appended to when new 
# collectors are found.
#
def buildCollectors(deposits, debits):
    temp = []

    with open(".collectors", "w") as f:
        
        # Skip collector input on deposits since they're all same class
        print("--- Beginning deposits ---")
        for line in deposits:
            temp.append([line[0], "deposit"])
            f.write(line[0].strip() + ", deposit\n")

        print("--- Beginning debits ---")
        for line in debits:
            collector_type = getCollectorInput(line)
            temp.append([line[0], collector_type])
            f.write(line[0].strip() + ", " + collector_type + "\n")


    return temp

#
# Helper function for build collectors. Prompts user for what kind of 
# classification should be applied to a collector and returns approved
# classification type. I would ultimately like to expand the user 
# interaction with this function: if the user doesn't recognize what
# the transaction is, print the most recent transaction with money spent
# and date. I want to avoid using the OOP with this project so I will
# side with a simpler approach.
#
def getCollectorInput(collector):
    answer = "???"

    # Emulate apt-get package manager style validation. Yes is 
    # default so allows user to type Y, y or press enter. Any
    # other input is treated as a "no". Iterate until user is
    # satisfied with class type for collector.
    while answer != "" and answer != "y" and answer != "Y":

        k = -1
        print("\n1. Deposit\n2. Miscellaneous\n3. Grocery\n4. Restaraunt\n5. Bill\n6. Coffee\n7. Savings\n0. Other\nPlease enter collector code for " + collector[0] + ": ", end = "")

        while k < 0 or k > 7:
            try:
                k = int(input())

                if (k < 0 or k > 7):
                    print("Invalid input, try again: ", end = "")

            except ValueError or TypeError:
                print("Invalid input, try again: ", end = "")
                k = -1


        if k == 0:
            collector_type = input("Please enter new type: ")
        else:
            collector_type = collector_types.get(k)
    
        answer = input("Set " + collector[0] + " as " + collector_type + " [Y]\\n?: ")


    return collector_type

#
# TODO: Parse deposits and debits for new collectors
#
# Builds a list of collectors from a file. Parses current list of deposits and
# debits to add new collectors if necessary.
#
def getCollectors(deposits, debits):
    collectors = []

    # Build list of collectors from file
    with open(".collectors", "r") as f:
        line = f.readline()

        while line:
            temp = line.split(", ")
            collectors.append(temp)

            line = f.readline()

    # Append to an existing file containing collectors
    with open(".collectors", "a") as f:
        for transaction in deposits:
            # If the collector isn't found in the list of collectors,
            # prompt user for collector type and append to file. I can
            # skip collector input for deposits since they are all the
            # same class.
            if not hasCollector(transaction[0], collectors):
                print("--- Adding new deposits ---")
                collectors.append([transaction[0], "deposit"])
                f.write(transaction[0].strip() + ", deposit\n")

        for transaction in debits:
            if not hasCollector(transaction[0], collectors):
                print("--- Found new debit ---")
                collector_type = getCollectorInput(transaction)
                collectors.append([transaction[0], collector_type])
                f.write(transaction[0].strip() + ", " + collector_type + "\n")

    return collectors 

#
# Helper function for get collector. Emulates Java .contains function for
# a list of collectors.
#
def hasCollector(collector, collectors):
    for line in collectors:
        if line[0] == collector:
            return True

    return False


def main():
    # Make sure we got valid input
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="name of raw USAA bank statement to be analyzed")
    args = parser.parse_args()
    
    if os.path.isfile(args.file_name):
        with open(args.file_name, "r") as f:
            line = f.readline()
           
            # Skip information I don't know how to handle yet
            while line:
                if line == "    DEPOSITS AND OTHER CREDITS\n":
                    break
                line = f.readline()
                    
            deposits = getTransactions(f, "    OTHER DEBITS\n")
            debits = getTransactions(f, " ACCOUNT BALANCE SUMMARY\n")
       

        # TODO: Check working directory for collectors file
        # If collectors file doesn't exist, build one
        if os.path.isfile(".collectors"):
            # Read from file
            print("Found collectors file")
            collectors = getCollectors(deposits, debits)
            
        else:
            # Build list 
            print("Collectors file not found, performing setup")
            collectors = buildCollectors(deposits, debits)

        classifiers = getClassifiers(collectors)

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
        

    else:
        print("Error: File " + args.file_name + " does not exist")


main()

