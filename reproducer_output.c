#include <stdio.h>
#include <string.h>

// Define a struct to represent a node
typedef struct Node {
    char label[20];
} Node;

// Function to validate and process a node
void validate_and_process(Node* node) {
    // Attempt to access the node's label, which will cause a NULL pointer dereference if node is NULL
    // This line reproduces the crash mechanism, as it tries to write to node->label when node is NULL
    strcpy(node->label, "example");
}

int main() {
    // Create a NULL pointer to a node
    Node* faulty_node = NULL;

    // Call the function with the NULL pointer, which will cause a NULL pointer dereference
    // This line reproduces the exact same crash mechanism as the original program
    validate_and_process(faulty_node);

    return 0;
}