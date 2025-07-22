/* ReadMe - to run:
 * assumes you have Node.js installed
 * npm install tsx
 * tsx fflottery_odds.ts
*/

interface Team {
    place: number;
    balls: number;
    eliminated: boolean;
    lockedPosition?: number; // Position this team is locked into due to protection rule
}

interface PickResult {
    pickNumber: number;
    winner: number;
    odds: { [place: number]: number };
    remainingBalls: number;
    lockedTeams: { place: number; position: number }[];
}

const initialOdds = [
    { place: 12, balls: 700 },
    { place: 11, balls: 330 },
    { place: 10, balls: 150 },
    { place: 9, balls: 120 },
    { place: 8, balls: 30 },
    { place: 7, balls: 20 }
]

class FantasyFootballLottery {
    private teams: Team[] = initialOdds.map(team => ({
        ...team,
        eliminated: false,
    }));

    private results: PickResult[] = [];
    private finalPositions: { [place: number]: number } = {}; // Maps team place to draft position

    // Protection rule: team can't fall more than 2 positions past expected
    private getWorstAllowedPosition(teamPlace: number): number {
        // Expected position is roughly their place ranking (12th place expects 1st pick, etc.)
        // But we need to account for the fact that only 6 teams are in lottery
        const expectedPosition = 13 - teamPlace; // 12th->1st, 11th->2nd, etc.
        return expectedPosition + 3; // Can fall at most 3 positions
    }

    // Reset simulation to initial state
    reset(): void {
        this.teams = initialOdds.map(team => ({
            ...team,
            eliminated: false,
        }));
        this.results = [];
        this.finalPositions = {};
    }

    // Check if any teams need to be locked into positions due to protection rule
    private checkAndLockTeams(currentPick: number): void {
        this.teams.forEach(team => {
            if (!team.eliminated && !team.lockedPosition) {
                const worstAllowed = this.getWorstAllowedPosition(team.place);

                // If this team would fall below their worst allowed position, lock them
                if (currentPick > worstAllowed) {
                    team.lockedPosition = worstAllowed;
                    team.eliminated = true; // Remove from lottery
                    this.finalPositions[team.place] = worstAllowed;
                }
            }
        });
    }

    // Get total remaining balls
    private getTotalBalls(): number {
        return this.teams
            .filter(team => !team.eliminated)
            .reduce((sum, team) => sum + team.balls, 0);
    }

    // Calculate current odds for each team
    private calculateOdds(): { [place: number]: number } {
        const totalBalls = this.getTotalBalls();
        const odds: { [place: number]: number } = {};

        this.teams.forEach(team => {
            if (!team.eliminated) {
                odds[team.place] = (team.balls / totalBalls) * 100;
            } else {
                odds[team.place] = 0;
            }
        });

        return odds;
    }

    // Get currently locked teams
    private getLockedTeams(): { place: number; position: number }[] {
        return this.teams
            .filter(team => team.lockedPosition !== undefined)
            .map(team => ({ place: team.place, position: team.lockedPosition! }));
    }

    // Simulate a single pick
    private simulatePick(pickNumber: number): PickResult {
        // First check if any teams need to be locked due to protection rule
        this.checkAndLockTeams(pickNumber);

        const totalBalls = this.getTotalBalls();
        const odds = this.calculateOdds();
        const lockedTeams = this.getLockedTeams();

        // If no teams remain in lottery, we're done
        if (totalBalls === 0) {
            return {
                pickNumber,
                winner: 0,
                odds: {},
                remainingBalls: 0,
                lockedTeams
            };
        }

        // Generate random number between 1 and totalBalls
        const randomBall = Math.floor(Math.random() * totalBalls) + 1;

        // Find which team owns this ball
        let currentSum = 0;
        let winner = 0;

        for (const team of this.teams) {
            if (!team.eliminated) {
                currentSum += team.balls;
                if (randomBall <= currentSum) {
                    winner = team.place;
                    break;
                }
            }
        }

        // Record the result
        const result: PickResult = {
            pickNumber,
            winner,
            odds,
            remainingBalls: totalBalls,
            lockedTeams
        };

        // Record final position and eliminate the winning team
        if (winner > 0) {
            this.finalPositions[winner] = pickNumber;
            this.eliminateTeamAndRedistribute(winner);
        }

        return result;
    }

    // Eliminate a team and redistribute their balls proportionally
    private eliminateTeamAndRedistribute(winnerPlace: number): void {
        const winnerTeam = this.teams.find(team => team.place === winnerPlace);
        if (!winnerTeam) return;

        const ballsToRedistribute = winnerTeam.balls;
        winnerTeam.eliminated = true;

        // Calculate total balls of remaining teams (before redistribution)
        const remainingTeams = this.teams.filter(team => !team.eliminated);
        const totalRemainingBalls = remainingTeams.reduce((sum, team) => sum + team.balls, 0);

        if (totalRemainingBalls === 0) return; // No teams left to redistribute to

        // Redistribute balls proportionally
        remainingTeams.forEach(team => {
            const proportion = team.balls / totalRemainingBalls;
            const additionalBalls = Math.round(ballsToRedistribute * proportion);
            team.balls += additionalBalls;
        });
    }

    // Assign remaining positions after lottery concludes
    private assignRemainingPositions(): void {
        const assignedPositions = new Set(Object.values(this.finalPositions));
        let nextPosition = 1;

        // Find the next available position
        while (assignedPositions.has(nextPosition) && nextPosition <= 6) {
            nextPosition++;
        }

        // Assign positions to teams that weren't picked and weren't locked
        this.teams.forEach(team => {
            if (this.finalPositions[team.place] === undefined) {
                // Find next available position
                while (assignedPositions.has(nextPosition) && nextPosition <= 6) {
                    nextPosition++;
                }
                if (nextPosition <= 6) {
                    this.finalPositions[team.place] = nextPosition;
                    assignedPositions.add(nextPosition);
                    nextPosition++;
                }
            }
        });
    }

    // Run a complete simulation for picks 1-6
    runSimulation(): { results: PickResult[], finalPositions: { [place: number]: number } } {
        this.reset();
        const results: PickResult[] = [];

        for (let pickNumber = 1; pickNumber <= 6; pickNumber++) {
            const result = this.simulatePick(pickNumber);
            results.push(result);
            this.results.push(result);

            // If no more teams in lottery, break
            if (result.remainingBalls === 0 && result.winner === 0) {
                break;
            }
        }

        this.assignRemainingPositions();

        return { results, finalPositions: { ...this.finalPositions } };
    }

    // Run multiple simulations and return statistics
    runMultipleSimulations(numSimulations: number): {
        pickStatistics: { [pickNumber: number]: { [place: number]: number } },
        finalPositionStats: { [place: number]: { [position: number]: number } },
        averageOdds: { [pickNumber: number]: { [place: number]: number } },
        protectionRuleStats: { [place: number]: number }
    } {
        const pickStatistics: { [pickNumber: number]: { [place: number]: number } } = {};
        const finalPositionStats: { [place: number]: { [position: number]: number } } = {};
        const protectionRuleStats: { [place: number]: number } = {};
        const oddsSum: { [pickNumber: number]: { [place: number]: number } } = {};

        // Initialize statistics objects
        for (let pick = 1; pick <= 6; pick++) {
            pickStatistics[pick] = {};
            oddsSum[pick] = {};
            [12, 11, 10, 9, 8, 7].forEach(place => {
                pickStatistics[pick][place] = 0;
                oddsSum[pick][place] = 0;
            });
        }

        [12, 11, 10, 9, 8, 7].forEach(place => {
            finalPositionStats[place] = {};
            protectionRuleStats[place] = 0;
            for (let pos = 1; pos <= 6; pos++) {
                finalPositionStats[place][pos] = 0;
            }
        });

        // Run simulations
        for (let sim = 0; sim < numSimulations; sim++) {
            const { results, finalPositions } = this.runSimulation();

            results.forEach(result => {
                if (result.winner > 0) {
                    // Count wins
                    pickStatistics[result.pickNumber][result.winner]++;
                }

                // Sum odds for averaging
                Object.entries(result.odds).forEach(([place, odds]) => {
                    oddsSum[result.pickNumber][parseInt(place)] += odds;
                });

                // Count protection rule activations
                result.lockedTeams.forEach(locked => {
                    protectionRuleStats[locked.place]++;
                });
            });

            // Record final positions
            Object.entries(finalPositions).forEach(([place, position]) => {
                finalPositionStats[parseInt(place)][position]++;
            });
        }

        // Calculate averages
        const averageOdds: { [pickNumber: number]: { [place: number]: number } } = {};
        for (let pick = 1; pick <= 6; pick++) {
            averageOdds[pick] = {};
            [12, 11, 10, 9, 8, 7].forEach(place => {
                averageOdds[pick][place] = oddsSum[pick][place] / numSimulations;
            });
        }

        return { pickStatistics, finalPositionStats, averageOdds, protectionRuleStats };
    }

    // Display results in markdown format
    displayResults(results: PickResult[], finalPositions: { [place: number]: number }): void {
        console.log('\n# Fantasy Football Lottery Simulation\n');

        results.forEach(result => {
            if (result.winner > 0) {
                console.log(`## Pick #${result.pickNumber} - Winner: ${result.winner}th place`);
                console.log(`**Remaining balls before pick:** ${result.remainingBalls}\n`);
            }

            if (result.lockedTeams.length > 0) {
                console.log('### 🔒 Teams locked by protection rule:');
                result.lockedTeams.forEach(locked => {
                    console.log(`- ${locked.place}th place locked into position ${locked.position}`);
                });
                console.log('');
            }

            if (Object.keys(result.odds).length > 0) {
                console.log('### Odds before pick:');
                console.log('| Team | Odds |');
                console.log('|------|------|');
                Object.entries(result.odds)
                    .sort(([a], [b]) => parseInt(b) - parseInt(a))
                    .forEach(([place, odds]) => {
                        if (odds > 0) {
                            console.log(`| ${place}th place | ${odds.toFixed(1)}% |`);
                        }
                    });
                console.log('');
            }
        });

        console.log('## Final Draft Positions\n');
        console.log('| Position | Team |');
        console.log('|----------|------|');
        Object.entries(finalPositions)
            .sort(([, a], [, b]) => a - b)
            .forEach(([place, position]) => {
                console.log(`| ${position} | ${place}th place |`);
            });
        console.log('');
    }

    // Display simulation statistics in markdown format
    displayStatistics(stats: any, numSimulations: number): void {
        console.log('## Initial Lottery Balls Distribution\n');
        console.log('| Team | Balls | Initial Odds |');
        console.log('|------|-------|--------------|');

        // Initial team setup (same as constructor)

        const totalInitialBalls = initialOdds.reduce((sum, team) => sum + team.balls, 0);

        initialOdds.forEach(team => {
            const initialOdds = (team.balls / totalInitialBalls) * 100;
            console.log(`| ${team.place}th place | ${team.balls} | ${initialOdds.toFixed(1)}% |`);
        });

        console.log(`\n**Total balls:** ${totalInitialBalls}\n`);


        console.log(`\n# Simulation Statistics (${numSimulations.toLocaleString()} simulations)\n`);

        console.log('## 📊 Final Position Distribution\n');
        // Create consolidated table header
        console.log('| Draft Position | 12th place | 11th place | 10th place | 9th place | 8th place | 7th place |');
        console.log('|---------------|------------|------------|------------|-----------|-----------|-----------|');

        // Create rows for each draft position
        for (let pos = 1; pos <= 6; pos++) {
            const row = [`| ${pos}`];
            [12, 11, 10, 9, 8, 7].forEach(place => {
                const count = stats.finalPositionStats[place][pos];
                const percentage = (count / numSimulations) * 100;
                row.push(`${percentage.toFixed(1)}%`);
            });
            console.log(row.join(' | ') + ' |');
        }
        console.log('');
    }
}

// Example usage
const lottery = new FantasyFootballLottery();

// Run a single simulation
// console.log('# Single Simulation Example');
// const { results: singleResult, finalPositions: singleFinal } = lottery.runSimulation();
// lottery.displayResults(singleResult, singleFinal);

// Run multiple simulations for statistics
console.log('\n---\n');
console.log('# Running Statistical Analysis...');
const stats = lottery.runMultipleSimulations(10000);
lottery.displayStatistics(stats, 10000);