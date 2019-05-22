#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

const int MAX_ABS = 1'000'000'000;

int main(int argc, char **argv){
    registerInteraction(argc, argv);

    int target = inf.readInt();
    int moves = inf.readInt();
    if (moves < 0) quitf(_fail, "invalid number of moves!");
    cout << moves << endl;
    while (true) {
        string tok = ouf.readToken();
        int value = ouf.readInt(-MAX_ABS, MAX_ABS);
        tout << tok << " " << value << endl;
        if (tok == "answer") {
            quitf(_ok, "got the answer. pass to checker");
        } else if (tok == "ask") {
            if (moves == 0) quitf(_wa, "ran out of moves");
            moves--;
            cout << value - target << endl;
        } else {
            quitf(_wa, "unknown action: %s", tok.c_str());
        }
    }
}
