def readIntegerInRange(minimum, maximum, prompt=''):
    while True:
        text = raw_input(prompt)
        try:
            num = int(text)
            if num in range(minimum, maximum):
                return num
            else: 
                print "Out of range [%s, %s), try again" % (minimum, maximum)
        except ValueError:
            print "Not an int, try again"