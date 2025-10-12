#include <vector>
using namespace std;

struct Comb
{
    long long MOD;
    std::vector<long long> fact, invFact;

    Comb(int n, long long mod = 1000000007LL) : MOD(mod)
    {
        fact.resize(n + 1);
        invFact.resize(n + 1);

        fact[0] = 1;
        for (int i = 1; i <= n; i++)
            fact[i] = fact[i - 1] * i % MOD;

        invFact[n] = modpow(fact[n], MOD - 2);

        for (int i = n - 1; i >= 0; i--)
            invFact[i] = invFact[i + 1] * (i + 1) % MOD;
    }

    long long modpow(long long a, long long b) const
    {
        long long res = 1;
        while (b)
        {
            if (b & 1)
                res = res * a % MOD;
            a = a * a % MOD;
            b >>= 1;
        }
        return res;
    }

    long long nCr(int n, int r) const
    {
        if (r < 0 || r > n)
            return 0;
        return fact[n] * invFact[r] % MOD * invFact[n - r] % MOD;
    }

    long long nPr(int n, int r) const
    {
        if (r < 0 || r > n)
            return 0;
        return fact[n] * invFact[n - r] % MOD;
    }

    long long nHr(int n, int r) const
    {
        // combinations with repetition: (n+r-1 choose r)
        if (n == 0 && r > 0)
            return 0;
        return nCr(n + r - 1, r);
    }

    long long catalan(int n) const
    {
        if (n == 0)
            return 1;
        return nCr(2 * n, n) * modpow(n + 1, MOD - 2) % MOD;
    }
};