#include <bits/stdc++.h>
using namespace std;

// ----------------- Shortcuts -----------------
#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);
using ull = unsigned long long;

// ----------------- Main Solve -----------------
void solve()
{
    ull x;
    std::cin >> x;
    ull res = 1;
    while (x > 3) {
        x /= 4;
        res *= 2;
    }
    std::cout << res << "\n";
}

int main()
{
    fastio();
    ull T = 1;
    cin >> T;
    while (T--) solve();
    return 0;
}
