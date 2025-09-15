#include <bits/stdc++.h>

using namespace std;

#define fastio                   \
    ios::sync_with_stdio(false); \
    std::cin.tie(0);             \
    std::cout.tie(0);
#define all(x) (x).begin(), (x).end()
#define pb push_back
#define int long long

std::string solve(std::string grick) {
    int l, r;
    std::cin >> l >> r;
    char c1, c2;
    std::cin >> c1 >> c2;

    l--;
    r--;

    for (int i = l ; i <= r ; i++) if (grick[i] == c1) grick[i] = c2;

    return grick;
}

int32_t main()
{
    fastio;

    int n, m;
    std::string grick;
    std::cin >> n >> m >> grick;

    while (m--) grick = solve(grick);

    std::cout << grick << "\n";

    return 0;
}
