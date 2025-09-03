// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";

/**
 * @title ArtworkDRM
 * @dev NFT contract with built-in licensing and royalty management
 */
contract ArtDRM is ERC721URIStorage, IERC2981, ReentrancyGuard, Ownable {
    
    // ==============================================
    // Data Structures
    // ==============================================
    
    struct ArtworkInfo {
        address creator;
        string metadataURI;
        uint256 royaltyPercentage; // Basis points (100 = 1%)
        bool isLicensed;
    }
    
    struct License {
        uint256 tokenId;
        address licensee;
        uint256 startDate;
        uint256 endDate;
        string termsHash; // IPFS hash of license terms
        LicenseType licenseType;
        bool isActive;
        uint256 feePaid;
    }
    
    enum LicenseType { PERSONAL, COMMERCIAL, EXCLUSIVE }
    
    // ==============================================
    // State Variables
    // ==============================================
    
    uint256 private _currentTokenId;
    uint256 public constant MAX_ROYALTY = 2000; // 20% in basis points
    uint256 public constant PLATFORM_FEE = 500; // 5% in basis points
    uint256 public constant LICENSE_FEE = 0.1 ether;
    
    mapping(uint256 => ArtworkInfo) public artworks;
    mapping(uint256 => License[]) public tokenLicenses;
    mapping(address => uint256[]) public creatorArtworks;
    
    uint256 private _licenseCounter;
    
    // ==============================================
    // Events
    // ==============================================
    
    event ArtworkRegistered(
        uint256 indexed tokenId,
        address indexed creator,
        string metadataURI,
        uint256 royaltyPercentage
    );
    
    event LicenseGranted(
        uint256 indexed licenseId,
        uint256 indexed tokenId,
        address indexed licensee,
        LicenseType licenseType,
        uint256 duration,
        uint256 feePaid
    );
    
    event LicenseRevoked(
        uint256 indexed licenseId,
        uint256 indexed tokenId,
        address indexed licensee
    );
    
    event RoyaltyPaid(
        uint256 indexed tokenId,
        address indexed creator,
        uint256 amount
    );
    
    // ==============================================
    // Constructor
    // ==============================================
    
    constructor() ERC721("ArtworkDRM", "ADRM") {
        _currentTokenId = 0;
        _licenseCounter = 0;
    }
    
    // ==============================================
    // Core Functionality
    // ==============================================
    
    /**
     * @dev Register a new artwork NFT
     * @param metadataURI IPFS URI containing artwork metadata
     * @param royaltyPercentage Royalty percentage in basis points (100 = 1%)
     */
    function registerArtwork(
        string memory metadataURI,
        uint256 royaltyPercentage
    ) external returns (uint256) {
        require(royaltyPercentage <= MAX_ROYALTY, "Royalty exceeds maximum");
        require(bytes(metadataURI).length > 0, "Metadata URI required");
        
        uint256 tokenId = _currentTokenId;
        _currentTokenId++;
        
        // Mint NFT to creator
        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, metadataURI);
        
        // Store artwork info
        artworks[tokenId] = ArtworkInfo({
            creator: msg.sender,
            metadataURI: metadataURI,
            royaltyPercentage: royaltyPercentage,
            isLicensed: false
        });
        
        // Track creator's artworks
        creatorArtworks[msg.sender].push(tokenId);
        
        emit ArtworkRegistered(tokenId, msg.sender, metadataURI, royaltyPercentage);
        
        return tokenId;
    }
    
    /**
     * @dev Grant a license for artwork usage
     * @param tokenId ID of the artwork token
     * @param licensee Address of the licensee
     * @param durationDays Duration of license in days
     * @param termsHash IPFS hash of license terms
     * @param licenseType Type of license (Personal, Commercial, Exclusive)
     */
    function grantLicense(
        uint256 tokenId,
        address licensee,
        uint256 durationDays,
        string memory termsHash,
        LicenseType licenseType
    ) external payable nonReentrant returns (uint256) {
        require(_exists(tokenId), "Artwork does not exist");
        require(ownerOf(tokenId) == msg.sender, "Only owner can grant license");
        require(licensee != address(0), "Invalid licensee address");
        require(msg.value >= LICENSE_FEE, "Insufficient license fee");
        require(durationDays > 0, "Duration must be positive");
        
        uint256 licenseId = _licenseCounter++;
        uint256 startDate = block.timestamp;
        uint256 endDate = startDate + (durationDays * 1 days);
        
        // Create license
        License memory newLicense = License({
            tokenId: tokenId,
            licensee: licensee,
            startDate: startDate,
            endDate: endDate,
            termsHash: termsHash,
            licenseType: licenseType,
            isActive: true,
            feePaid: msg.value
        });
        
        tokenLicenses[tokenId].push(newLicense);
        artworks[tokenId].isLicensed = true;
        
        // Transfer license fee to artwork owner
        payable(msg.sender).transfer(msg.value);
        
        emit LicenseGranted(licenseId, tokenId, licensee, licenseType, durationDays, msg.value);
        
        return licenseId;
    }
    
    /**
     * @dev Revoke a license
     * @param tokenId ID of the artwork token
     * @param licensee Address of the licensee
     */
    function revokeLicense(uint256 tokenId, address licensee) external {
        require(_exists(tokenId), "Artwork does not exist");
        require(ownerOf(tokenId) == msg.sender, "Only owner can revoke license");
        
        License[] storage licenses = tokenLicenses[tokenId];
        bool found = false;
        
        for (uint256 i = 0; i < licenses.length; i++) {
            if (licenses[i].licensee == licensee && licenses[i].isActive) {
                licenses[i].isActive = false;
                found = true;
                emit LicenseRevoked(i, tokenId, licensee);
                break;
            }
        }
        
        require(found, "Active license not found");
        
        // Check if artwork still has active licenses
        bool hasActiveLicense = false;
        for (uint256 i = 0; i < licenses.length; i++) {
            if (licenses[i].isActive && block.timestamp <= licenses[i].endDate) {
                hasActiveLicense = true;
                break;
            }
        }
        
        artworks[tokenId].isLicensed = hasActiveLicense;
    }
    
    /**
     * @dev Handle sale with automatic royalty distribution
     * @param tokenId ID of the artwork token
     * @param salePrice Price of the sale
     */
    function handleSale(uint256 tokenId, uint256 salePrice) external payable nonReentrant {
        require(_exists(tokenId), "Artwork does not exist");
        require(msg.value >= salePrice, "Insufficient payment");
        
        address currentOwner = ownerOf(tokenId);
        address creator = artworks[tokenId].creator;
        
        if (currentOwner == creator) {
            // Primary sale - creator gets full amount minus platform fee
            uint256 platformFee = (salePrice * PLATFORM_FEE) / 10000;
            uint256 creatorAmount = salePrice - platformFee;
            
            payable(creator).transfer(creatorAmount);
            payable(owner()).transfer(platformFee);
        } else {
            // Secondary sale - pay royalty to creator
            uint256 royaltyAmount = (salePrice * artworks[tokenId].royaltyPercentage) / 10000;
            uint256 sellerAmount = salePrice - royaltyAmount;
            
            payable(creator).transfer(royaltyAmount);
            payable(currentOwner).transfer(sellerAmount);
            
            emit RoyaltyPaid(tokenId, creator, royaltyAmount);
        }
        
        // Transfer ownership would be handled separately
    }
    
    // ==============================================
    // View Functions
    // ==============================================
    
    /**
     * @dev Get artwork information
     */
    function getArtworkInfo(uint256 tokenId) 
        external 
        view 
        returns (address creator, string memory metadataURI, uint256 royaltyPercentage, bool isLicensed) 
    {
        require(_exists(tokenId), "Artwork does not exist");
        ArtworkInfo memory artwork = artworks[tokenId];
        return (artwork.creator, artwork.metadataURI, artwork.royaltyPercentage, artwork.isLicensed);
    }
    
    /**
     * @dev Get active licenses for a token
     */
    function getActiveLicenses(uint256 tokenId) external view returns (License[] memory) {
        require(_exists(tokenId), "Artwork does not exist");
        
        License[] memory allLicenses = tokenLicenses[tokenId];
        uint256 activeCount = 0;
        
        // Count active licenses
        for (uint256 i = 0; i < allLicenses.length; i++) {
            if (allLicenses[i].isActive && block.timestamp <= allLicenses[i].endDate) {
                activeCount++;
            }
        }
        
        // Create array of active licenses
        License[] memory activeLicenses = new License[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < allLicenses.length; i++) {
            if (allLicenses[i].isActive && block.timestamp <= allLicenses[i].endDate) {
                activeLicenses[index] = allLicenses[i];
                index++;
            }
        }
        
        return activeLicenses;
    }
    
    /**
     * @dev Get artworks created by an address
     */
    function getCreatorArtworks(address creator) external view returns (uint256[] memory) {
        return creatorArtworks[creator];
    }
    
    /**
     * @dev Get current token ID (total number of artworks)
     */
    function getCurrentTokenId() external view returns (uint256) {
        return _currentTokenId;
    }
    
    /**
     * @dev Check if a license is valid
     */
    function isLicenseValid(uint256 tokenId, address licensee) external view returns (bool) {
        require(_exists(tokenId), "Artwork does not exist");
        
        License[] memory licenses = tokenLicenses[tokenId];
        for (uint256 i = 0; i < licenses.length; i++) {
            if (licenses[i].licensee == licensee && 
                licenses[i].isActive && 
                block.timestamp <= licenses[i].endDate) {
                return true;
            }
        }
        return false;
    }
    
    // ==============================================
    // EIP-2981 Royalty Standard
    // ==============================================
    
    /**
     * @dev See {IERC2981-royaltyInfo}
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        external
        view
        override
        returns (address receiver, uint256 royaltyAmount)
    {
        require(_exists(tokenId), "Artwork does not exist");
        
        address creator = artworks[tokenId].creator;
        uint256 royaltyPercentage = artworks[tokenId].royaltyPercentage;
        uint256 royalty = (salePrice * royaltyPercentage) / 10000;
        
        return (creator, royalty);
    }
    
    // ==============================================
    // Emergency Functions
    // ==============================================
    
    /**
     * @dev Emergency function to update platform fee (only owner)
     */
    function updatePlatformFee(uint256 newFee) external onlyOwner {
        require(newFee <= 1000, "Platform fee too high"); // Max 10%
        // Would emit event and update fee
    }
    
    /**
     * @dev Withdraw contract balance (only owner)
     */
    function withdrawBalance() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance to withdraw");
        payable(owner()).transfer(balance);
    }
    
    // ==============================================
    // Interface Support
    // ==============================================
    
    /**
     * @dev See {IERC165-supportsInterface}
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, IERC165)
        returns (bool)
    {
        return interfaceId == type(IERC2981).interfaceId || super.supportsInterface(interfaceId);
    }
}