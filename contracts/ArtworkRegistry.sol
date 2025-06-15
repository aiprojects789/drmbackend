// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";

contract ArtworkRegistry is ERC721, Ownable, IERC2981 {
    using Strings for uint256;

    struct Artwork {
        address creator;
        string metadataURI;
        uint256 royaltyPercentage;
        bool isLicensed;
    }

    uint256 public tokenCount;
    mapping(uint256 => Artwork) private _artworks;
    mapping(uint256 => string) private _tokenURIs;
    address public licensingContract;

    event ArtworkRegistered(uint256 indexed tokenId, address indexed creator, string metadataURI, uint256 royaltyPercentage);
    event LicenseStatusChanged(uint256 indexed tokenId, bool isLicensed);

    modifier onlyLicensingContract() {
        require(msg.sender == licensingContract, "Caller is not licensing contract");
        _;
    }

    constructor() ERC721("ArtDRM", "ADRM") {}

    function setLicensingContract(address _licensingContract) external onlyOwner {
        licensingContract = _licensingContract;
    }

    function updateLicenseStatus(uint256 tokenId, bool status) external onlyLicensingContract {
        require(_exists(tokenId), "Nonexistent token");
        _artworks[tokenId].isLicensed = status;
        emit LicenseStatusChanged(tokenId, status);
    }


    function currentTokenId() public view returns (uint256) {
        return tokenCount;
    }

    function registerArtwork(
    address owner,
    string memory metadataURI,
    uint256 royaltyPercentage
) public returns (uint256) {
    require(royaltyPercentage <= 20, "Royalty cannot exceed 20%");
    
    uint256 tokenId = tokenCount;
    _safeMint(owner, tokenId);
    _setTokenURI(tokenId, metadataURI);
    
    _artworks[tokenId] = Artwork({
        creator: msg.sender,
        metadataURI: metadataURI,
        royaltyPercentage: royaltyPercentage,
        isLicensed: false
    });

    tokenCount++; // Increment after all operations are successful
    emit ArtworkRegistered(tokenId, msg.sender, metadataURI, royaltyPercentage);
    return tokenId;
    }

    function getArtworkInfo(uint256 tokenId) public view returns (
        address creator,
        string memory metadataURI,
        uint256 royaltyPercentage,
        bool isLicensed
    ) {
        require(_exists(tokenId), "Nonexistent token");
        Artwork memory artwork = _artworks[tokenId];
        return (
            artwork.creator,
            artwork.metadataURI,
            artwork.royaltyPercentage,
            artwork.isLicensed
        );
    }

    function royaltyInfo(
        uint256 tokenId,
        uint256 salePrice
    ) external view override returns (address receiver, uint256 royaltyAmount) {
        require(_exists(tokenId), "Nonexistent token");
        Artwork memory artwork = _artworks[tokenId];
        royaltyAmount = (salePrice * artwork.royaltyPercentage) / 100;
        return (artwork.creator, royaltyAmount);
    }

    function _setTokenURI(uint256 tokenId, string memory _tokenURI) internal virtual {
        require(_exists(tokenId), "Nonexistent token");
        _tokenURIs[tokenId] = _tokenURI;
    }

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        require(_exists(tokenId), "Nonexistent token");
        return _tokenURIs[tokenId];
    }

    // Add this function to replace getTokenCounter()
    function getCurrentTokenId() public view returns (uint256) {
     return tokenCount;
}


}