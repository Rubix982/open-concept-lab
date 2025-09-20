#include <iostream>
#include <math.h>
using namespace std;
using ull = unsigned long long;

#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);

void solve()
{
    ull x, y, z;
    std::cin >> x >> y >> z;
    std::cout << x + y + z - 1 << "\n";
}

int main()
{
    fastio();
    int T = 1;
    cin >> T;
    while (T--)
        solve();
    return 0;
}
