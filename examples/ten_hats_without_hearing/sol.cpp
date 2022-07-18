#include <iostream>
#include <cassert>
using namespace std;
typedef long long ll;

constexpr int n = 10;
int main(int argc, char **argv) {
    int i = atoi(argv[1]);
    assert(0 <= i && i < n);
    int t;
    for (cin >> t; t; t--) {
        string s;
        cin >> s;
        cout << char(s[i ^ 1] ^ (('R' ^ 'B') * (i & 1))) << endl;
    }
}
