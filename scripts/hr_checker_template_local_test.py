from __future__ import division, print_function, unicode_literals, absolute_import















{template}















def make_obj(**kwargs):
    # hacky af
    x = lambda: 1
    for k, v in kwargs.items():
        setattr(x, k, v)
    return x

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Judge for the problem.')
    parser.add_argument('input_file', help='Input file name.')
    parser.add_argument('output_file', help="Contestant's file name.")
    parser.add_argument('judge_file', help='Judge auxiliary data file name.')
    args = parser.parse_args()

    import re
    test_id = int(re.search(r'\d+', args.input_file).group(0))
    print("Checking the output...")
    t_obj = make_obj(
            testcase_signal=0,
            testcase_input_path=args.input_file,
            testcase_output_path=args.output_file,
            testcase_expected_output_path=args.judge_file,
            submission_code_path='foobar',
            testcase_id=test_id,
            testcase_result=True,
        )
    r_obj = make_obj()
    run_custom_checker(t_obj, r_obj)

    print("Result:", r_obj.result)
    print("Score:", r_obj.score)
    print("Message:", r_obj.message)
