#include <bits/stdc++.h>
using namespace std;
// g++-15 -std=c++17 -O2 -Wall 897_A.cpp -o 897_A

// ----------------- Shortcuts -----------------
#define fastio()                 \
    ios::sync_with_stdio(false); \
    cin.tie(nullptr);
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define pb emplace_back
#define fi first
#define se second

// ----------------- Main Solve -----------------
void solve(std::string T)
{
    char need = 'a';

    for (char &c : T) {
        if (c <= need) {
            c = need;
            need++;
        }
        if (need > 'z') break;
    }

    if (need <= 'z') cout << "-1\n";
    else cout << T << "\n";
}

int main()
{
    fastio();
    // Read a file with multiple test cases, with a string on each line
    std::string T;
    while (std::getline(std::cin, T))
    {
        solve(T);
    }
}
