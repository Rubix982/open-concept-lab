/*
A. Problemsolving Log
time limit per test2 seconds
memory limit per test256 megabytes

Monocarp is participating in a programming contest, which features 26
 problems, named from 'A' to 'Z'. The problems are sorted by difficulty. Moreover, it's known that Monocarp can solve problem 'A' in 1
 minute, problem 'B' in 2
 minutes, ..., problem 'Z' in 26
 minutes.

After the contest, you discovered his contest log — a string, consisting of uppercase Latin letters, such that the 𝑖-th letter tells which problem Monocarp was solving during the 𝑖-th minute of the contest. If Monocarp had spent enough time in total on a problem to solve it, he solved it. Note that Monocarp could have been thinking about a problem after solving it.

Given Monocarp's contest log, calculate the number of problems he solved during the contest.

Input

The first line contains a single integer 𝑡(1≤𝑡≤100) — the number of testcases.

The first line of each testcase contains a single integer 𝑛(1≤𝑛≤500) — the duration of the contest, in minutes.

The second line contains a string of length exactly 𝑛, consisting only of uppercase Latin letters, — Monocarp's contest log.

Output
For each testcase, print a single integer — the number of problems Monocarp solved during the contest.

Example

Input
3
6
ACBCBC
7
AAAAFPC
22
FEADBBDFFEDFFFDHHHADCC

Output
3
1
4
*/

#include <bits/stdc++.h>

using namespace std;

#define fastio                   \
    ios::sync_with_stdio(false); \
    std::cin.tie(0);                  \
    std::cout.tie(0);
#define all(x) (x).begin(), (x).end()
#define pb push_back
#define int long long

void solve()
{
    int contest_length;
    std::cin >> contest_length;

    string contest_log;
    std::cin >> contest_log;

    int i = 0;
    std::array<int, 26> problem_times;
    for (char c : s) problem_times[c - 'A']++;

    int problems_solved = 0;
    for (int i = 0; i < contest_length; i++)
    {
        if (problem_times[i] >= i + 1) problems_solved++;
    }

    std::cout << problems_solved << "\n";
}

int32_t main()
{
    fastio;

    int t;
    std::cin >> t;
    while (t--)
    {
        solve();
    }

    return 0;
}
