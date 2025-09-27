#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include <limits>
using namespace std;

// 2D point structure
struct Point {
    double x, y;
};

// Utility function: cross product of vectors OA and OB
// Returns positive for counter-clockwise turn, negative for clockwise, 0 if collinear.
double cross(const Point &O, const Point &A, const Point &B) {
    return (A.x - O.x) * (B.y - O.y) - (A.y - O.y) * (B.x - O.x);
}

// Utility function: distance squared between two points
double distSq(const Point &A, const Point &B) {
    double dx = A.x - B.x;
    double dy = A.y - B.y;
    return dx*dx + dy*dy;
}

// *******************************************************
// Convex Hull: Graham Scan
// *******************************************************
vector<Point> convexHullGraham(vector<Point> &pts) {
    int n = pts.size();
    if (n < 3) return pts;  // A hull is not defined for fewer than 3 points
    // Find the point with the lowest y-coordinate (and lowest x if tie)
    int lowest = 0;
    for (int i = 1; i < n; i++) {
        if (pts[i].y < pts[lowest].y ||
            (pts[i].y == pts[lowest].y && pts[i].x < pts[lowest].x)) {
            lowest = i;
        }
    }
    swap(pts[0], pts[lowest]);
    // Sort points by polar angle with respect to pts[0], using cross product
    Point pivot = pts[0];
    sort(pts.begin() + 1, pts.end(), [&](const Point &a, const Point &b) {
        double c = cross(pivot, a, b);
        if (fabs(c) < 1e-9) {
            // If collinear, put closer point first
            return distSq(pivot, a) < distSq(pivot, b);
        }
        return c > 0;
    });
    // Remove collinear points at the end of sorted list (keeping the farthest)
    vector<Point> filtered;
    filtered.push_back(pts[0]);
    for (int i = 1; i < n; ++i) {
        while (i < n-1 && fabs(cross(pivot, pts[i], pts[i+1])) < 1e-9) {
            i++;
        }
        filtered.push_back(pts[i]);
    }
    // Build hull with Graham scan
    vector<Point> hull;
    for (const auto &p : filtered) {
        while (hull.size() >= 2 &&
               cross(hull[hull.size()-2], hull[hull.size()-1], p) <= 0) {
            hull.pop_back();
        }
        hull.push_back(p);
    }
    return hull;
}

// *******************************************************
// Convex Hull: Jarvis March (Gift Wrapping)
// *******************************************************
vector<Point> convexHullJarvis(vector<Point> &pts) {
    int n = pts.size();
    if (n < 3) return pts;
    vector<Point> hull;
    // Find leftmost point
    int leftmost = 0;
    for (int i = 1; i < n; i++) {
        if (pts[i].x < pts[leftmost].x) {
            leftmost = i;
        }
    }
    int p = leftmost;
    do {
        hull.push_back(pts[p]);
        int q = (p+1) % n;
        for (int i = 0; i < n; i++) {
            double c = cross(pts[p], pts[q], pts[i]);
            // Choose point i if it is more counterclockwise than current q
            if (c < 0 ||
                (fabs(c) < 1e-9 && distSq(pts[p], pts[i]) > distSq(pts[p], pts[q]))) {
                q = i;
            }
        }
        p = q;
    } while (p != leftmost);
    return hull;
}

// *******************************************************
// Convex Hull: Chan's Algorithm (output-sensitive)
// *******************************************************
// Chan's algorithm runs in O(n log h) time by combining Graham Scan and Jarvis March.
vector<Point> convexHullChan(vector<Point> pts) {
    int n = pts.size();
    if (n < 3) return pts;
    // Sort points lexicographically by x, then y
    sort(pts.begin(), pts.end(), [](const Point &a, const Point &b) {
        return (a.x < b.x) || (a.x == b.x && a.y < b.y);
    });
    int m = 1;
    // Find initial guess for m as a power of 2 >= 3
    while (m*m < n) m *= 2;
    vector<Point> hull;
    while (true) {
        int numGroups = (n + m - 1) / m;
        vector<vector<Point>> hulls(numGroups);
        // Compute convex hull of each group of at most m points
        for (int i = 0; i < numGroups; ++i) {
            int start = i * m;
            int end = min(start + m, n);
            vector<Point> subset(pts.begin() + start, pts.begin() + end);
            hulls[i] = convexHullGraham(subset);
        }
        // Jarvis march merging step
        hull.clear();
        // Find the starting point among all hulls (lowest y, then x)
        Point startP = pts[0];
        for (int i = 0; i < numGroups; ++i) {
            for (const auto &p : hulls[i]) {
                if (p.y < startP.y || (p.y == startP.y && p.x < startP.x)) {
                    startP = p;
                }
            }
        }
        Point pointOnHull = startP;
        int hullPoints = 0;
        do {
            hull.push_back(pointOnHull);
            Point nextPoint = {numeric_limits<double>::infinity(), numeric_limits<double>::infinity()};
            // Find the most counterclockwise point among all hulls
            for (int i = 0; i < numGroups; ++i) {
                for (const auto &candidate : hulls[i]) {
                    if (candidate.x == pointOnHull.x && candidate.y == pointOnHull.y) continue;
                    double c = cross(pointOnHull, nextPoint, candidate);
                    if (nextPoint.x == numeric_limits<double>::infinity() ||
                        c < 0 ||
                        (fabs(c) < 1e-9 && distSq(pointOnHull, candidate) > distSq(pointOnHull, nextPoint))) {
                        nextPoint = candidate;
                    }
                }
            }
            pointOnHull = nextPoint;
            hullPoints++;
            // If we have wrapped more points than allowed, increase m and retry
            if (hullPoints > m) {
                m *= 2;
                break;
            }
        } while (!(pointOnHull.x == startP.x && pointOnHull.y == startP.y));
        if (hullPoints <= m) break;
    }
    return hull;
}

// *******************************************************
// Rotating Calipers: Diameter (farthest pair) of a convex polygon
// *******************************************************
// Returns the distance of the farthest pair of points (the diameter) in a convex polygon.
double convexPolygonDiameter(const vector<Point> &hull) {
    int n = hull.size();
    if (n < 2) return 0;
    int j = 1;
    double maxDistSq = 0;
    // For each vertex i, find farthest point j such that distance is maximal
    for (int i = 0; i < n; ++i) {
        int ni = (i + 1) % n;
        // Move j to the farthest point from edge (i, ni)
        while (abs(cross(hull[i], hull[ni], hull[(j+1) % n])) >
               abs(cross(hull[i], hull[ni], hull[j]))) {
            j = (j + 1) % n;
        }
        maxDistSq = max(maxDistSq, distSq(hull[i], hull[j]));
        maxDistSq = max(maxDistSq, distSq(hull[ni], hull[j]));
    }
    return sqrt(maxDistSq);
}

// *******************************************************
// Delaunay Triangulation (Bowyer-Watson algorithm)
// *******************************************************
// Triangle structure for Delaunay triangulation
struct Triangle {
    Point a, b, c;
};
// Check if point p is inside the circumcircle of triangle t
bool inCircumcircle(const Triangle &t, const Point &p) {
    double ax = t.a.x - p.x, ay = t.a.y - p.y;
    double bx = t.b.x - p.x, by = t.b.y - p.y;
    double cx = t.c.x - p.x, cy = t.c.y - p.y;
    double det = (ax * ax + ay * ay) * (bx * cy - cx * by)
               - (bx * bx + by * by) * (ax * cy - cx * ay)
               + (cx * cx + cy * cy) * (ax * by - bx * ay);
    return det > 0;
}
vector<Triangle> delaunayTriangulation(vector<Point> pts) {
    int n = pts.size();
    if (n < 3) return {};
    // Compute bounding values for super-triangle
    double minX = pts[0].x, minY = pts[0].y, maxX = pts[0].x, maxY = pts[0].y;
    for (auto &p : pts) {
        minX = min(minX, p.x);
        minY = min(minY, p.y);
        maxX = max(maxX, p.x);
        maxY = max(maxY, p.y);
    }
    double dx = maxX - minX, dy = maxY - minY;
    double dmax = max(dx, dy);
    Point mid = { (minX + maxX) / 2, (minY + maxY) / 2 };
    // Create a super-triangle that encompasses all points
    Triangle superTri = {
        { mid.x - 2*dmax, mid.y - dmax },
        { mid.x,         mid.y + 2*dmax },
        { mid.x + 2*dmax, mid.y - dmax }
    };
    vector<Triangle> triangulation = { superTri };
    // Bowyer-Watson: add one point at a time
    for (auto &p : pts) {
        vector<pair<Point, Point>> polygon;
        vector<Triangle> newTris;
        // Find triangles whose circumcircles contain p
        for (auto &tri : triangulation) {
            if (inCircumcircle(tri, p)) {
                // Add triangle edges to polygon (may have duplicates)
                polygon.push_back({tri.a, tri.b});
                polygon.push_back({tri.b, tri.c});
                polygon.push_back({tri.c, tri.a});
            } else {
                newTris.push_back(tri);
            }
        }
        // Remove duplicate edges from polygon
        auto removeDuplicateEdges = [](vector<pair<Point, Point>> &edges) {
            vector<bool> toRemove(edges.size(), false);
            for (size_t i = 0; i < edges.size(); ++i) {
                for (size_t j = i+1; j < edges.size(); ++j) {
                    if (edges[i].first.x == edges[j].second.x && edges[i].first.y == edges[j].second.y &&
                        edges[i].second.x == edges[j].first.x && edges[i].second.y == edges[j].first.y) {
                        toRemove[i] = toRemove[j] = true;
                    }
                }
            }
            vector<pair<Point, Point>> filtered;
            for (size_t i = 0; i < edges.size(); ++i) {
                if (!toRemove[i]) {
                    filtered.push_back(edges[i]);
                }
            }
            edges.swap(filtered);
        };
        removeDuplicateEdges(polygon);
        // Form new triangles with point p
        for (auto &edge : polygon) {
            Triangle tri = { edge.first, edge.second, p };
            newTris.push_back(tri);
        }
        triangulation.swap(newTris);
    }
    // Remove triangles that include any vertex of the super-triangle
    triangulation.erase(
        remove_if(triangulation.begin(), triangulation.end(), [&](const Triangle &tri) {
            return (tri.a.x < minX || tri.a.x > maxX || tri.a.y < minY || tri.a.y > maxY ||
                    tri.b.x < minX || tri.b.x > maxX || tri.b.y < minY || tri.b.y > maxY ||
                    tri.c.x < minX || tri.c.x > maxX || tri.c.y < minY || tri.c.y > maxY);
        }),
        triangulation.end()
    );
    return triangulation;
}

// *******************************************************
// Line Segment Intersection
// *******************************************************
// Checks if two line segments AB and CD intersect.
bool segmentsIntersect(const Point &A, const Point &B, const Point &C, const Point &D) {
    auto onSegment = [](const Point &p, const Point &q, const Point &r) {
        return q.x <= max(p.x, r.x) + 1e-9 && q.x >= min(p.x, r.x) - 1e-9 &&
               q.y <= max(p.y, r.y) + 1e-9 && q.y >= min(p.y, r.y) - 1e-9;
    };
    auto orientation = [](const Point &p, const Point &q, const Point &r) {
        double val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y);
        if (fabs(val) < 1e-9) return 0;  // collinear
        return (val > 0) ? 1 : 2;        // 1 = clockwise, 2 = counterclockwise
    };
    int o1 = orientation(A, B, C);
    int o2 = orientation(A, B, D);
    int o3 = orientation(C, D, A);
    int o4 = orientation(C, D, B);
    // General case
    if (o1 != o2 && o3 != o4) return true;
    // Special Cases
    if (o1 == 0 && onSegment(A, C, B)) return true;
    if (o2 == 0 && onSegment(A, D, B)) return true;
    if (o3 == 0 && onSegment(C, A, D)) return true;
    if (o4 == 0 && onSegment(C, B, D)) return true;
    return false;
}

// *******************************************************
// Point in Polygon (Ray Casting)
// *******************************************************
// Returns true if point p is inside the polygon (or on its boundary).
bool isPointInPolygon(const vector<Point> &polygon, const Point &p) {
    bool inside = false;
    int n = polygon.size();
    for (int i = 0, j = n-1; i < n; j = i++) {
        const Point &pi = polygon[i];
        const Point &pj = polygon[j];
        bool intersect = ((pi.y > p.y) != (pj.y > p.y)) &&
                         (p.x < (pj.x - pi.x) * (p.y - pi.y) / (pj.y - pi.y) + pi.x);
        if (intersect) inside = !inside;
    }
    return inside;
}

// *******************************************************
// Closest Pair of Points (Divide and Conquer)
// *******************************************************
// Helper for recursive closest pair.
double closestPairRec(vector<Point> &pts, int left, int right) {
    if (right - left <= 3) {
        double minDist = numeric_limits<double>::infinity();
        for (int i = left; i <= right; ++i) {
            for (int j = i+1; j <= right; ++j) {
                minDist = min(minDist, sqrt(distSq(pts[i], pts[j])));
            }
        }
        sort(pts.begin()+left, pts.begin()+right+1, [](const Point &a, const Point &b){
            return a.y < b.y;
        });
        return minDist;
    }
    int mid = (left + right) / 2;
    double midX = pts[mid].x;
    double d1 = closestPairRec(pts, left, mid);
    double d2 = closestPairRec(pts, mid+1, right);
    double d = min(d1, d2);
    inplace_merge(pts.begin()+left, pts.begin()+mid+1, pts.begin()+right+1,
                  [](const Point &a, const Point &b){ return a.y < b.y; });
    vector<Point> strip;
    for (int i = left; i <= right; ++i) {
        if (fabs(pts[i].x - midX) < d) strip.push_back(pts[i]);
    }
    double minDist = d;
    int m = strip.size();
    for (int i = 0; i < m; ++i) {
        for (int j = i+1; j < m && (strip[j].y - strip[i].y) < d; ++j) {
            minDist = min(minDist, sqrt(distSq(strip[i], strip[j])));
        }
    }
    return minDist;
}
// Main closest pair function: sorts points by x and calls recursive function.
double closestPair(vector<Point> pts) {
    sort(pts.begin(), pts.end(), [](const Point &a, const Point &b){
        return a.x < b.x;
    });
    return closestPairRec(pts, 0, pts.size() - 1);
}

// *******************************************************
// Axis-Aligned Bounding Box (AABB)
// *******************************************************
// Returns a pair of Points (min corner and max corner) of the bounding box.
pair<Point, Point> computeAABB(const vector<Point> &pts) {
    if (pts.empty()) return {{0,0}, {0,0}};
    double minX = pts[0].x, minY = pts[0].y;
    double maxX = pts[0].x, maxY = pts[0].y;
    for (auto &p : pts) {
        minX = min(minX, p.x);
        minY = min(minY, p.y);
        maxX = max(maxX, p.x);
        maxY = max(maxY, p.y);
    }
    Point minP = { minX, minY };
    Point maxP = { maxX, maxY };
    return { minP, maxP };
}

// *******************************************************
// Example Usage
// *******************************************************
int main() {
    vector<Point> points = {{0,0}, {1,1}, {2,2}, {2,0},
                            {2,4}, {3,3}, {0,5}, {4,0}};
    auto hullGraham = convexHullGraham(points);
    auto hullJarvis = convexHullJarvis(points);
    auto hullChan   = convexHullChan(points);
    double diameter = convexPolygonDiameter(hullGraham);
    auto triangulation = delaunayTriangulation(points);
    bool intersect = segmentsIntersect({0,0},{2,2},{0,2},{2,0});
    bool inside    = isPointInPolygon(points, {1,1});
    double closest  = closestPair(points);
    auto bbox       = computeAABB(points);

    cout << "Graham Hull size: " << hullGraham.size() << endl;
    cout << "Jarvis Hull size: " << hullJarvis.size() << endl;
    cout << "Chan Hull size: "   << hullChan.size() << endl;
    cout << "Polygon diameter: " << diameter << endl;
    cout << "Delaunay triangles: " << triangulation.size() << endl;
    cout << "Segments intersect: " << intersect << endl;
    cout << "Point inside polygon: " << inside << endl;
    cout << "Closest pair distance: " << closest << endl;
    cout << "AABB min: (" << bbox.first.x << ", " << bbox.first.y << ")" << endl;
    cout << "AABB max: (" << bbox.second.x << ", " << bbox.second.y << ")" << endl;
    return 0;
}
