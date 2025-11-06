#include<iostream>
#include<algorithm>
#include<vector>

int main(){
    // read n and j
    int n, j;
    std::cin >> n >> j;

    // Make a vector of all cards 1,2,3,4,....,13,14,15
    std::vector<int> cards = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};

    // shuffling the cards
    std::random_shuffle(cards.begin(), cards.end());

    // laying out these cards in this order
    for (int card : cards){
        // reading winnable card in the middle (and ignoring it)
        int w;
        std::cin >> w;

        // play this card
        std::cout << card << std::endl;

        // reading the cards the other players played (and ignoring it)
        std::vector<int> playedCards(n);
        for (int i = 0; i < n; i++){
            std::cin >> playedCards[i];
        }
    }
}
