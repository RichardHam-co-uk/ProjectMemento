const { main } = require('../src/index');

describe('Project Memento Initialization', () => {
    test('should log initialization message', () => {
        const consoleSpy = jest.spyOn(console, 'log');
        main();
        expect(consoleSpy).toHaveBeenCalledWith('Project Memento is initialized and ready for development.');
        consoleSpy.mockRestore();
    });
});
