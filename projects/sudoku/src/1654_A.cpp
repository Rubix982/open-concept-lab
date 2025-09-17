#include <bits/stdc++.h>
using namespace std;
#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);
// g++-15 -std=c++17 -O2 -Wall 897_A.cpp -o 897_A

using ll = long long;

void solve()
{
    int n;
    cin >> n;
    vector<ll> a(n);
    for (int i = 0; i < n; i++)
        cin >> a[i];

    // original maximum adjacent sum
    ll orig = 0;
    for (int i = 0; i + 1 < n; ++i)
        orig = max(orig, a[i] + a[i + 1]);

    // prefix max and suffix max arrays
    vector<ll> pref(n), suf(n);
    pref[0] = a[0];
    for (int i = 1; i < n; ++i)
        pref[i] = max(pref[i - 1], a[i]);
    suf[n - 1] = a[n - 1];
    for (int i = n - 2; i >= 0; --i)
        suf[i] = max(suf[i + 1], a[i]);

    // max over a[r] + max_{0..r-1} a[p]
    ll best1 = 0;
    for (int r = 1; r < n; ++r)
        best1 = max(best1, a[r] + pref[r - 1]);

    // max over a[l] + max_{l+1..n-1} a[q]
    ll best2 = 0;
    for (int l = 0; l + 1 < n; ++l)
        best2 = max(best2, a[l] + suf[l + 1]);

    cout << max({orig, best1, best2}) << '\n';
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
