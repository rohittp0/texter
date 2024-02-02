import socket
import dnslib
import requests


def request_content(domain: str):
    domain = domain.replace("-", "/")
    request = requests.get(f"https://{domain}")

    if request.status_code == 200:
        return request.text

    request = requests.get(f"http://{domain}")

    if request.status_code == 200:
        return request.text

    return f"HTTP {request.status_code} - {request.reason}"


def split_data(data: str, chunk_size: int = 250):
    """
    Splits data into chunks with a maximum size of chunk_size.
    Prepends each chunk with its sequence number (e.g., '0_', '1_', ...).
    """
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    prefixed_chunks = [f"{i}_{chunk}" for i, chunk in enumerate(chunks)]
    return prefixed_chunks


def handle_dns_request(data):
    request = dnslib.DNSRecord.parse(data)

    # Create a DNS response
    response = dnslib.DNSRecord(dnslib.DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

    # Check if the query is for a TXT record
    for question in request.questions:
        if question.qtype == dnslib.QTYPE.TXT:
            # Fetch the content and split it into chunks
            domain_data = request_content(str(question.qname))
            chunks = split_data(domain_data)

            # Add each chunk as a separate TXT record
            for chunk in chunks:
                response.add_answer(dnslib.RR(question.qname, dnslib.QTYPE.TXT, rdata=dnslib.TXT(chunk), ttl=1))

    return response.pack()


def main():
    # Bind a socket to UDP port 53
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('0.0.0.0', 5353))  # Remember to use a different port if 53 is not available
        print("DNS Server is running")

        try:
            while True:
                data, address = server_socket.recvfrom(512)
                response = handle_dns_request(data)
                server_socket.sendto(response, address)
        except KeyboardInterrupt:
            print("DNS Server is stopping")


if __name__ == '__main__':
    main()
