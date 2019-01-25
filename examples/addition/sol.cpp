#include <bits/stdc++.h>

using namespace std;
typedef long long ll;

void solve() {
    int n;
    scanf("%d", &n);
    ll s = 0;
    while (n--) {
        ll v;
        scanf("%lld", &v);
        s += v;
    }
    printf("%lld\n", s);
}
int main() {
    int z;
    for (scanf("%d", &z); z--; solve());
}