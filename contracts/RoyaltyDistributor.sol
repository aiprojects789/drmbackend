// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/interfaces/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";

contract RoyaltyDistributor {
    address public marketplace;
    IERC20 public paymentToken;

    event RoyaltyDistributed(
        uint256 indexed tokenId,
        address indexed creator,
        address indexed seller,
        uint256 royaltyAmount,
        uint256 sellerAmount
    );

    event PrimarySaleDistributed(
        uint256 indexed tokenId,
        address indexed creator,
        address indexed buyer,
        uint256 creatorAmount,
        uint256 platformFee
    );

    constructor(address _marketplace, address _paymentToken) {
        marketplace = _marketplace;
        paymentToken = IERC20(_paymentToken);
    }

    function distributeRoyalty(
        uint256 tokenId,
        address nftContract,
        address seller,
        uint256 salePrice
    ) external {
        require(msg.sender == marketplace, "Unauthorized");
        
        (address creator, uint256 royaltyAmount) = IERC2981(nftContract).royaltyInfo(tokenId, salePrice);
        uint256 sellerAmount = salePrice - royaltyAmount;
        
        paymentToken.transferFrom(msg.sender, creator, royaltyAmount);
        paymentToken.transferFrom(msg.sender, seller, sellerAmount);

        emit RoyaltyDistributed(tokenId, creator, seller, royaltyAmount, sellerAmount);
    }

    function distributePrimarySale(
        uint256 tokenId,
        address nftContract,
        address buyer,
        uint256 salePrice
    ) external {
        require(msg.sender == marketplace, "Unauthorized");
        
        // Get royalty info but only use creator address
        (address creator, ) = IERC2981(nftContract).royaltyInfo(tokenId, salePrice);
        uint256 platformFee = salePrice / 20; // 5% platform fee
        uint256 creatorAmount = salePrice - platformFee;
        
        paymentToken.transferFrom(buyer, creator, creatorAmount);
        paymentToken.transferFrom(buyer, marketplace, platformFee);

        emit PrimarySaleDistributed(tokenId, creator, buyer, creatorAmount, platformFee);
    }
}