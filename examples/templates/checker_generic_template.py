from kg.checkers import * ### @import

@checker
def check(input_stream, output_stream, judge_stream, **kwargs):
    # write your grader here
    
    # Raise this if the answer is incorrect
    raise Wrong("The contestant's output is incorrect!")
    
    # Raise this if the judge data is incorrect, or if the checking fails for some reason other than Wrong
    # Any other exception type raised will be considered equivalent to Fail.
    # Any 'Fail' verdict must be investigated since it indicates a problem with the checker/data/etc.
    raise Fail("The judge data is incorrect. Fix it!")

    # the return value is the score, and must be a value between 0.0 and 1.0
    return 1.0 

if __name__ == '__main__': check_files(check)
