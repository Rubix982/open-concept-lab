#include <bits/stdc++.h>
using namespace std;

// ----------------- Shortcuts -----------------
#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define pb emplace_back
#define fi first
#define se second

using ll = long long;
using ull = unsigned long long;
using ld = long double;
using pii = pair<int, int>;
using pll = pair<ll, ll>;
using i128 = __int128;

// ----------------- Constants -----------------
const ll MOD = 998244353;
const ll MOD2 = 1000000007;
const ll INF = (ll)4e18;
const int MAXN = 2e5 + 5;

// ----------------- Math Utils -----------------
ll modpow(ll a, ll b, ll m = MOD)
{
    ll res = 1;
    while (b)
    {
        if (b & 1)
            res = res * a % m;
        a = a * a % m;
        b >>= 1;
    }
    return res;
}
ll modinv(ll a, ll m = MOD) { return modpow(a, m - 2, m); }

template <class T>
inline void chkmax(T &x, T y)
{
    if (y > x)
        x = y;
}
template <class T>
inline void chkmin(T &x, T y)
{
    if (y < x)
        x = y;
}

// Safe modular add/sub
inline ll addmod(ll x, ll y, ll m = MOD)
{
    x += y;
    return (x >= m ? x - m : x);
}
inline ll submod(ll x, ll y, ll m = MOD)
{
    x -= y;
    return (x < 0 ? x + m : x);
}

// gcd/lcm shortcuts
inline ll gcdll(ll a, ll b) { return b ? gcdll(b, a % b) : a; }
inline ll lcmll(ll a, ll b) { return a / gcdll(a, b) * b; }

// factorials / nCr (modular) ------------------
vector<ll> fact, invfact;
void init_factorials(int n, ll m = MOD)
{
    fact.assign(n + 1, 1);
    invfact.assign(n + 1, 1);
    for (int i = 1; i <= n; i++)
        fact[i] = fact[i - 1] * i % m;
    invfact[n] = modinv(fact[n], m);
    for (int i = n; i > 0; i--)
        invfact[i - 1] = invfact[i] * i % m;
}
ll nCr(int n, int r, ll m = MOD)
{
    if (r < 0 || r > n)
        return 0;
    return fact[n] * invfact[r] % m * invfact[n - r] % m;
}

// ----------------- Debugging -----------------
#ifdef LOCAL
template <class T>
void _print(const T &x);
template <class A, class B>
ostream &operator<<(ostream &os, const pair<A, B> &p)
{
    return os << '(' << p.fi << ',' << p.se << ')';
}
template <class T>
ostream &operator<<(ostream &os, const vector<T> &v)
{
    os << '{';
    string sep = "";
    for (auto &x : v)
        os << sep << x, sep = ",";
    return os << '}';
}
template <class T>
ostream &operator<<(ostream &os, const set<T> &s)
{
    os << '{';
    string sep = "";
    for (auto &x : s)
        os << sep << x, sep = ",";
    return os << '}';
}
#define debug(x) cerr << #x << " = " << (x) << '\n'
#else
#define debug(x)
#endif

// ----------------- Main Solve -----------------
void solve()
{
    // example:
    // int n; cin >> n;
    // vector<int> a(n); for (auto &x : a) cin >> x;
    // cout << "answer\n";
}

int main()
{
    fastio();
    int T = 1;
    cin >> T;
    while (T--) solve();
    return 0;
}
