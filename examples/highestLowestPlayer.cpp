#include<iostream>
#include<vector>

int main(){
    //read n and j
    int n, j;
    std::cin >> n >> j;
    // your cards
    std::vector<int> cards = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
    // repeating for the whole game
    while (true){
        int value;
        std::cin >> value;

        if (value>0){
            // choose the highest card, so the last one since the list is ordered
            std::cout << cards.back() << std::endl;
            cards.pop_back();
        }
        else {
            // choose the lowest card
            std::cout << cards.front() << std::endl;
            cards.erase(cards.begin());
        }


        // reading the input but ignoring it
        std::vector<int> submitted_numbers(n);
        for (int i = 0; i < n; i++) {
          std::cin >> submitted_numbers[i];
        }
    }
}