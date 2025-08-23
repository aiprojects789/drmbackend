const { ethers } = require("hardhat");

async function main() {
  console.log("🚀 Starting ArtDRM deployment...");

  const [deployer] = await ethers.getSigners();
  const { chainId } = await ethers.provider.getNetwork();
  console.log(`📡 Connected to network with chain ID: ${chainId}`);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`👤 Deployer address: ${deployer.address}`);
  console.log(`💰 Deployer balance: ${ethers.formatEther(balance)} ETH`);

  const ArtDRM = await ethers.getContractFactory("ArtDRM");
  const artDRM = await ArtDRM.deploy();
  await artDRM.waitForDeployment();

  console.log(`✅ ArtDRM deployed at: ${await artDRM.getAddress()}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
