"""
Encryption Utility for BYOK API Keys

Uses Fernet symmetric encryption to securely store user LLM API keys.
"""

import os
from cryptography.fernet import Fernet
from typing import Optional


class KeyEncryption:
    """Handle encryption/decryption of API keys."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption handler.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from ENCRYPTION_KEY env var.
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY not set. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def encrypt(self, api_key: str) -> str:
        """
        Encrypt an API key.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Encrypted key as base64 string
        """
        encrypted = self.cipher.encrypt(api_key.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """
        Decrypt an API key.
        
        Args:
            encrypted_key: Encrypted key as base64 string
            
        Returns:
            Plain text API key
        """
        decrypted = self.cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()


# Singleton instance
_encryptor: Optional[KeyEncryption] = None


def get_encryptor() -> KeyEncryption:
    """Get or create encryption handler singleton."""
    global _encryptor
    if _encryptor is None:
        _encryptor = KeyEncryption()
    return _encryptor


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Encrypted key
    """
    return get_encryptor().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key from storage.
    
    Args:
        encrypted_key: Encrypted key
        
    Returns:
        Plain text API key
    """
    return get_encryptor().decrypt(encrypted_key)


# CLI utility for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Generate key: python encryption.py generate")
        print("  Encrypt:      python encryption.py encrypt <api_key>")
        print("  Decrypt:      python encryption.py decrypt <encrypted_key>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        # Generate new encryption key
        key = Fernet.generate_key()
        print(f"Generated encryption key (add to .env):")
        print(f"ENCRYPTION_KEY={key.decode()}")
    
    elif command == "encrypt":
        if len(sys.argv) < 3:
            print("Error: API key required")
            sys.exit(1)
        
        api_key = sys.argv[2]
        encrypted = encrypt_api_key(api_key)
        print(f"Encrypted: {encrypted}")
    
    elif command == "decrypt":
        if len(sys.argv) < 3:
            print("Error: Encrypted key required")
            sys.exit(1)
        
        encrypted_key = sys.argv[2]
        try:
            decrypted = decrypt_api_key(encrypted_key)
            print(f"Decrypted: {decrypted}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
