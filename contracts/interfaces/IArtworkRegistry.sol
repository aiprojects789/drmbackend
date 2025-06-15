// contracts/interfaces/IArtworkRegistry.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IArtworkRegistry {
    function getRoyaltyInfo(uint256 tokenId) external view returns (address, uint256);
}