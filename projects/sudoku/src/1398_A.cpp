#include <iostream>
#include <cmath>
#include <vector>
#include <algorithm>

using namespace std;
// g++-15 -std=c++17 -O2 -Wall 897_A.cpp -o 897_A

// ----------------- Shortcuts -----------------
#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);

void solve()
{
    int n;
    cin >> n;
    vector<int> a(n);
    for (int i = 0; i < n; i++)
        cin >> a[i];

    int x = a[0];
    int y = a[1];
    int z = a[n - 1];
    if (z >= (x + y))
        std::cout << 1 << " " << 2 << " " << n - 1 << "\n";
    else
        cout << -1 << "\n";
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
