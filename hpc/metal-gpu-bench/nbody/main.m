/*
 * main.m — N-body entry point
 *
 * AppKit requires an NSApplication to be running before any windows appear.
 * We create a minimal app delegate, instantiate NBodySimulator, and hand
 * control to [simulator runLoop] which starts the CVDisplayLink + NSApp loop.
 *
 * Controls:
 *   G     — toggle CPU / GPU mode
 *   Q/Cmd-W — quit
 *
 * Command-line args:
 *   --n <count>   particle count (default 4096)
 */

#import <Cocoa/Cocoa.h>
#import "NBodySimulator.h"

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (nonatomic, assign) NSUInteger N;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)note
{
    (void)note;

    /* Parse --n from argv before NSApp swallows arguments */
    NSArray *args = [[NSProcessInfo processInfo] arguments];
    NSUInteger N  = 4096;
    for (NSUInteger i = 1; i + 1 < args.count; i++) {
        if ([args[i] isEqualToString:@"--n"])
            N = (NSUInteger)[args[i+1] integerValue];
    }

    NSLog(@"N-body: N=%lu  (use --n <count> to change)", (unsigned long)N);
    NSLog(@"Press G to toggle CPU / GPU mode.");

    NBodySimulator *sim = [[NBodySimulator alloc] initWithN:N];
    [sim runLoop];   /* blocks until window is closed */
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)app
{
    (void)app; return YES;
}

@end

int main(int argc, const char *argv[])
{
    (void)argc; (void)argv;
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        AppDelegate   *del = [[AppDelegate alloc] init];
        [app setDelegate:del];
        [app run];
    }
    return 0;
}
