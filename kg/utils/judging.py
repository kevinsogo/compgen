import functools, json

from .utils import * ### @import

class ParseError(Exception): ...
class Wrong(Exception): ...
class Fail(Exception): ...

WA = Wrong
# TODO add deprecation notice when WA is raised. can't use "deprec_alias" because WA needs to be raisable ### @rem

class Verdict:
    AC = "Success"
    
    # wrong answer due to invalid/unreadable format. ### @rem
    PAE = "Wrong answer (Parse error)"
    
    # the solution didn't compile ### @rem
    CE = "Compile Error"
    
    # correct output format, incorrect answer. ### @rem
    WA = "Wrong answer"
    
    # solution crashed. ### @rem
    RTE = "Runtime Error"
    
    # solution didn't finish under the specified time limit. ### @rem
    TLE = "Time Limit Exceeded"
    
    # unintended errors of the checker/interactor. ### @rem
    EXC = "Checker/Interactor raised an error [BAD!]"
    
    # deliberate failures, e.g., if the test data is detected as incorrect. ### @rem
    FAIL = "Checker/Interactor failed [BAD!]"


polygon_rcode = {
    Verdict.AC: 0,
    Verdict.CE: 1,
    Verdict.PAE: 2,
    Verdict.WA: 1,
    Verdict.RTE: 1,
    Verdict.TLE: 1,
    Verdict.FAIL: 3,
    Verdict.EXC: 3,
}
polygon_partial = 16

kg_rcode = {
    Verdict.AC: 0,
    Verdict.CE: 11,
    Verdict.WA: 21,
    Verdict.RTE: 22,
    Verdict.TLE: 23,
    Verdict.PAE: 24,
    Verdict.FAIL: 31,
    Verdict.EXC: 32,
}


### @@ if format == 'dom' {
domjudge_rcode = {
    Verdict.AC: 42,
    Verdict.CE: 43,
    Verdict.PAE: 43,
    Verdict.WA: 43,
    Verdict.RTE: 43,
    Verdict.TLE: 43,
    Verdict.FAIL: 3,
    Verdict.EXC: 3,
}
### @@ }


xml_outcome = {
    Verdict.AC: "Accepted",
    Verdict.CE: "No - Compilation Error",
    Verdict.PAE: "No - Wrong Answer",
    Verdict.WA: "No - Wrong Answer",
    Verdict.RTE: "No - Run-time Error",
    Verdict.TLE: "No - Time Limit Exceeded",
    Verdict.FAIL: "No - Other - Contact Staff",
    Verdict.EXC: "No - Other - Contact Staff",
}

hr_verdict_name = {
    Verdict.AC: "Success",
    Verdict.CE: "Compilation Error",
    Verdict.PAE: "Wrong Answer",
    Verdict.WA: "Wrong Answer",
    Verdict.RTE: "Runtime Error",
    Verdict.TLE: "Time limit exceeded", # I don't like HR's message "terminated due to timeout"
    Verdict.FAIL: "Checker Failed",
    Verdict.EXC: "Checker Failed.", # Added a dot so we can recognize which kind of failure it is.
}


def write_json_verdict(verdict, message, score, result_file):
    with open(result_file, 'w') as f:
        json.dump({'verdict': verdict, 'message': message, 'score': float(score)}, f)

def write_xml_verdict(verdict, message, score, result_file):
    from xml.etree.ElementTree import Element, ElementTree
    result = Element('result')
    result.set('security', result_file)
    result.set('outcome', xml_outcome[verdict])
    result.text = str(verdict) + ": " + message
    ElementTree(result).write(result_file, xml_declaration=True, encoding="utf-8")


def minimum_score(scores, mn=0.0, mx=1.0, break_on_min=False, exc=Fail):
    if mn > mx: raise exc(f"Invalid arguments for mn and mx: {mn} > {mx}")
    m = mx
    to_exit = lambda: break_on_min and m == mn
    if not to_exit():
        for score in scores:
            if score is None:
                raise exc("A score of 'None' was returned.")
            if not (mn <= score <= mx):
                raise exc(f"Invalid score: {score}. It must be in the interval [{mn}, {mx}].")
            m = min(m, score)
            if to_exit(): break # we can stop now
    return m


def average_score(scores, exc=Fail):
    tl = ct = 0
    for score in scores:
        if score is None: raise exc("A score of 'None' was returned.")
        tl += score
        ct += 1
    if ct == 0: raise exc("Cannot take average of empty score list")
    return tl / ct



def on_exhaust(exc):
    def _d(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except StopIteration as st:
                raise exc from st
        return _f
    return _d



