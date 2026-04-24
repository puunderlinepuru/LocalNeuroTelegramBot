package stuff;

import java.io.*;
import java.net.*;

public class Client {

    public static void send(String message) {
        String hostName = "localhost";
        int portNumber = 12345;
        try (
                Socket echoSocket = new Socket(hostName, portNumber);
                PrintWriter out = new PrintWriter(echoSocket.getOutputStream(), true)
//                BufferedReader in = new BufferedReader(new InputStreamReader(echoSocket.getInputStream()));
        ) {
            String formattedMessage = message + "\r\n\r\n";
            out.println(formattedMessage);
        } catch (UnknownHostException e) {
            System.err.println("Don't know about host " + hostName);
            System.exit(1);
        } catch (IOException e) {
            System.err.println("Couldn't get I/O for the connection to " +
                    hostName);
            System.exit(1);
        }
    }
}