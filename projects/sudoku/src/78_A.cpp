#include <iostream>
using namespace std;

int main()
{
    string first, second, third;
    std::getline(std::cin, first);
    std::getline(std::cin, second);
    std::getline(std::cin, third);
    int count = 0;
    for (char c : first)
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u')
            count++;

    if (count != 5)
    {
        cout << "NO\n";
        return 0;
    }
    count = 0;

    for (char c : second)
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u')
            count++;

    if (count != 7)
    {
        cout << "NO\n";
        return 0;
    }

    count = 0;

    for (char c : third)
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u')
            count++;

    if (count != 5)
    {
        cout << "NO\n";
        return 0;
    }

    cout << "YES\n";

    return 0;
}
