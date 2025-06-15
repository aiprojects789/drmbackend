const hre = require("hardhat");

async function main() {
  // ===== 1. DEPLOY CONTRACTS =====
  const ArtworkRegistry = await hre.ethers.getContractFactory("ArtworkRegistry");
  const registry = await ArtworkRegistry.deploy();
  await registry.waitForDeployment();
  console.log("ArtworkRegistry deployed to:", await registry.getAddress());

  // ===== 2. SIMULATE ARTIST ACTIONS =====
  console.log("\n=== Artist minting new artwork ===");
  const [artist, buyer] = await hre.ethers.getSigners();
  
  // Mint artwork with 10% royalty
  const tx = await registry.registerArtwork(
    artist.address,
    "ipfs://QmXyZ...", // Fake IPFS hash
    10 // 10% royalty
  );
  const receipt = await tx.wait();
  const tokenId = receipt.logs[0].args.tokenId;
  console.log(`Minted artwork #${tokenId} to ${artist.address}`);

  // ===== 3. SHOW ROYALTY INFO =====
  console.log("\n=== Checking royalty info ===");
  const [creator, royalty] = await registry.getRoyaltyInfo(tokenId);
  console.log(`Creator: ${creator}, Royalty: ${royalty}%`);

  // ===== 4. SIMULATE SALE =====
  console.log("\n=== Simulating secondary sale ===");
  console.log(`Transferring artwork #${tokenId} to buyer ${buyer.address}...`);
  await registry.connect(artist).transferFrom(artist.address, buyer.address, tokenId);
  console.log("Transfer complete!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});