/*
 * main.m — Heat Stencil entry point
 *
 * Controls:
 *   G       — toggle CPU / GPU mode
 *   R       — reset grid to initial conditions
 *   Q/Cmd-W — quit
 *
 * Command-line args:
 *   --w <width>   grid width  (default 512)
 *   --h <height>  grid height (default 512)
 */

#import <Cocoa/Cocoa.h>
#import "StencilSimulator.h"

@interface AppDelegate : NSObject <NSApplicationDelegate>
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)note
{
    (void)note;
    NSArray *args = [[NSProcessInfo processInfo] arguments];
    NSUInteger W = 512, H = 512;
    for (NSUInteger i = 1; i + 1 < args.count; i++) {
        if ([args[i] isEqualToString:@"--w"]) W = (NSUInteger)[args[i+1] integerValue];
        if ([args[i] isEqualToString:@"--h"]) H = (NSUInteger)[args[i+1] integerValue];
    }

    NSLog(@"Heat stencil: %lu×%lu  (--w / --h to change)", W, H);
    NSLog(@"Press G to toggle CPU/GPU.");

    StencilSimulator *sim = [[StencilSimulator alloc] initWithWidth:W height:H];
    [sim runLoop];
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
